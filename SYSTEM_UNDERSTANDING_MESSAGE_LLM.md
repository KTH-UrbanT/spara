# SPARA System Understanding

This document explains how SPARA currently works with a focus on the `message-service` and `llm-service`.
It is based on the code paths that are actually used by the Docker startup files in `infra/`.

## 1. High-Level Summary

SPARA is built as a small distributed system with clear service boundaries:

- `frontend` is the browser client.
- `message-service` is the public backend. It owns HTTP APIs, Socket.IO, JWT-based REST auth, PostgreSQL persistence, and the live chat bridge to Redis.
- `llm-service` is not a public API service. It is a background Redis worker that reacts to chat events, runs LLM-driven routing and retrieval, and writes assistant replies back into Redis.
- `redis` is the live coordination bus and short-term working memory.
- `message_store` is PostgreSQL and acts as the durable store for users, sessions, messages, and ratings.

The shortest mental model is:

1. The frontend sends a user message to `message-service` over Socket.IO.
2. `message-service` writes the user message to PostgreSQL and Redis.
3. `message-service` publishes a Redis event on `thread_events`.
4. `llm-service` consumes that event, reads the thread history from Redis, generates an answer, and appends the assistant reply to the same Redis thread.
5. `message-service` notices the assistant reply in Redis, persists the assistant text to PostgreSQL, and emits the updated session back to the frontend.

## 2. How the System Starts

### Development startup

The main development stack is defined in `infra/docker-compose.dev.yml`.

Startup order is:

1. `redis`
2. `message_store` (PostgreSQL)
3. `message-service`
4. `llm-service`
5. `frontend`
6. `pgadmin`

Important details:

- Redis is exposed on `6379`.
- PostgreSQL is exposed on `5432`.
- PostgreSQL runs `shared/db/init.sql` at first initialization.
- `message-service` is exposed on `8000`.
- `llm-service` is internal only. It has no published port in the main compose file.
- `frontend` is exposed on `5173` and points to `http://localhost:8000` and `ws://localhost:8000`.

### Production startup

`infra/docker-compose.prod.yml` follows the same overall pattern with a few differences:

- The services are attached to an external Docker network called `spara_network`.
- PostgreSQL is mapped to host port `5433`.
- The frontend is built with production URLs pointing to `https://sparabot.com` and `wss://sparabot.com`.
- The frontend is served on host port `8800`.
- `llm-service` uses `Dockerfile` instead of `Dockerfile.dev`.

### Service entrypoints

The Docker entrypoints that matter most for this document are:

- `message-service/Dockerfile`
  - starts `uvicorn main:socket_app --host 0.0.0.0 --port 8000`
- `message-service/main.py`
  - imports `socket_app` from `socket_manager/app.py`
  - imports `events.handlers` for Socket.IO event registration side effects
- `llm-service/Dockerfile` and `llm-service/Dockerfile.dev`
  - both start `python generation.py`
- `llm-service/generation.py`
  - creates `RedisQueueManager()` and starts `event_listener()`

This means the current production path is:

- FastAPI + Socket.IO for `message-service`
- Redis pub/sub worker for `llm-service`

Notably, `llm-service` is currently a worker process, not an HTTP API.

## 3. Core State Stores

SPARA splits state across PostgreSQL and Redis.

### PostgreSQL: durable system of record

Initialized by `shared/db/init.sql`.

Main tables:

- `users`
- `sessions`
- `messages`
- `ratings`

Important schema meaning:

- `sessions.session_token` is not just a random token. In practice it becomes the chat thread identifier used by the frontend and Redis.
- `messages` stores only `session_id`, `role`, `content`, and `sent_at`.
- `ratings` are attached to assistant messages through the `messages.message_id` foreign key.

### Redis: live thread memory and coordination

Redis is used for message exchange, agent metadata, session state, and report artifacts.

Important keys and channels:

| Key or channel | Type | Purpose |
| --- | --- | --- |
| `thread:{session_token}:messages` | list | Live chat thread history used by both services |
| `thread_events` | pub/sub channel | Notification bus that a thread changed |
| `thread:{thread_id}:meta` | hash | LLM-side metadata such as address, expert handoff flags, and other cross-turn state |
| `session:{thread_id}` | string containing JSON list | Building-agent session-state history |
| `draft_report:{report_id}` | string with TTL | Downloadable report payload for the draft-report flow |

This split matters because PostgreSQL and Redis do not store the same fields.

## 4. Message Service Deep Dive

### What the message service owns

The `message-service` is the user-facing backend. It owns:

- REST endpoints for users, sessions, messages, ratings, and report downloads
- JWT creation and JWT verification for REST requests
- Socket.IO connection handling
- PostgreSQL persistence
- Redis mirroring of live conversation state
- polling Redis for assistant replies

### Startup path inside the service

The runtime path is:

1. `main.py` loads `socket_app`
2. `socket_manager/app.py` builds:
   - a FastAPI app
   - a Socket.IO `AsyncServer`
   - a shared Redis client
   - CORS configuration
   - REST router registration
3. On FastAPI startup, `ensure_rating_table_exists()` is run

The app includes:

- REST endpoints from `service/entrypoints.py`
- socket event handlers from `events/handlers.py`

### REST API responsibilities

`service/entrypoints.py` defines the main HTTP API.

Key capabilities:

- user registration and login
- temporary user support
- session lookup
- message history lookup
- manual message insertion
- ratings
- downloading draft reports

#### Authentication model

REST endpoints use `AuthorizationService`, which issues and validates JWT bearer tokens.

The JWT contains:

- `user_id`
- `email`
- `temporary_user`
- expiry

The REST layer checks ownership before returning sessions, messages, ratings, or downloadable reports.

### WebSocket responsibilities

The live chat path is defined in `events/handlers.py`.

Main socket events:

- `connect`
- `disconnect`
- `establish_session`
- `create_session`
- `send_message`
- internal `session_updated` emissions
- internal `answer_message` emissions

#### New chat flow

When the user starts a new chat:

1. The frontend opens a temporary socket without a session id.
2. It emits `create_session(message, user_id)`.
3. `message-service` inserts a new database session with:
   - `user_id`
   - `session_token = sid`
   - `is_active = True`
4. It emits `session_created` back to the client with:
   - `session_id` as the socket `sid`
   - `session_id_int` as the database primary key
5. The frontend stores that pair and uses `session_id` as the route/thread id.

This is a key design detail:

- the Redis thread id and frontend chat id are the database `session_token`
- the database `session_id` integer is only the relational primary key

#### Existing chat connection flow

When the user opens an existing chat:

1. The frontend sets Socket.IO auth data:
   - `session_id`
   - `session_id_int`
   - `user_id`
2. On `connect`, the backend:
   - joins the socket room named after `session_id`
   - loads the existing messages from PostgreSQL using `session_id_int`
   - pushes them into Redis using `insert_into_redis_client(...)`
   - emits `session_updated`

This means Redis is rebuilt from PostgreSQL when the user reconnects to a session.

#### Sending a message

The core live path is `send_message(sid, data, session_id, session_id_int)`.

What it does:

1. Validates that the message, `session_id`, and `session_id_int` are present.
2. Builds a user message payload:
   - `content`
   - `role = user`
   - `timestamp`
   - `added_to_database = 0`
3. Appends that payload to Redis list `thread:{session_id}:messages`.
4. Inserts the same user message into PostgreSQL.
5. Emits `session_updated` so the frontend sees the new local state.
6. Publishes a Redis event on `thread_events`.
7. Polls Redis waiting for an assistant reply.
8. Once it sees an assistant message at the end of the Redis thread:
   - inserts the assistant text into PostgreSQL
   - emits `session_updated`
   - emits `answer_message`

This is the handoff point into `llm-service`.

#### Rehydration logic

`service/redis.py` contains `insert_into_redis_client(...)`, which tries to:

- avoid duplicate messages when a thread already exists in Redis
- merge `message_id`, `rating`, and `version` back into Redis messages
- preserve ordering by timestamp

This is an important bridge because PostgreSQL is durable, while Redis is the live conversation buffer.

### What the frontend depends on from message-service

The frontend uses:

- REST for auth, session listing, ratings, and report download
- Socket.IO for live session creation, live updates, and live assistant replies

Important frontend behavior:

- `session_updated` is the main event used to render the full message list
- the frontend expects assistant messages may include:
  - `sources`
  - `downloadable_report`
  - rating metadata

That matters because not all of those fields are persisted to PostgreSQL.

## 5. LLM Service Deep Dive

### What the LLM service really is

Despite the name, the current `llm-service` is not a web API in the Dockerized system.
It is a Redis event worker.

Its job is:

- subscribe to `thread_events`
- read the relevant Redis thread
- decide how to answer the latest user message
- run the appropriate LLM/retrieval/database logic
- append the assistant message back to Redis

### Startup path

Current startup path:

1. `generation.py` imports `RedisQueueManager` from `src/redis/redis_manager.py`
2. `RedisQueueManager()`:
   - connects to Redis with retry logic
   - constructs `AgentRouter()`
3. `event_listener()` subscribes to `thread_events`
4. the process blocks listening forever

There is no port exposure and no HTTP router in the current startup path.

### Redis event consumption

The worker reacts to any message published on `thread_events`.

For each event:

1. It extracts `thread_id`
2. Reads `thread:{thread_id}:messages`
3. If the last message is not from the user, it ignores the event
4. Reads metadata from `thread:{thread_id}:meta`
5. Calls `AgentRouter.route_message(messages, last_message, metadata, thread_id)`
6. Appends the returned assistant payload to `thread:{thread_id}:messages`
7. Writes updated metadata back to `thread:{thread_id}:meta`
8. Publishes another `thread_events` notification

The republish is safe because the follow-up event is ignored when the last thread message is from the assistant.

### AgentRouter responsibilities

`src/pipeline/agent_router.py` is the main control plane for LLM behavior.

Its job is to route a user turn into one of several behaviors:

- expert handoff confirmation handling
- draft energy report generation
- expert handoff request
- generic question handling
- building-specific handling
- cluster handling
- conversational handling

#### Expert handoff state

The router uses Redis metadata to remember whether the assistant is waiting for a yes/no confirmation before sending an expert email.

Metadata flags include:

- `expert_handoff_pending_confirmation`
- `expert_handoff_requested`
- `expert_handoff_sent`
- `expert_handoff_error`

#### Draft report path

If the router detects a report request, it calls `generate_draft_report_response(...)`.

That flow:

1. loads building session state from Redis key `session:{thread_id}`
2. gathers address, building identifiers, and building facts
3. asks an OpenAI-based response agent to draft a report
4. falls back to a deterministic report if the model call fails
5. stores the generated artifact in Redis with a 30-minute TTL
6. returns an assistant message containing `downloadable_report`

The frontend later uses the REST endpoint in `message-service` to download that artifact.

#### Expert handoff email path

If the router detects that the user wants human escalation:

1. it first asks for confirmation
2. if the user confirms, it sends an SMTP email to the configured recipient
3. the email contains:
   - an LLM-generated or fallback summary
   - the full transcript as a text attachment

## 6. Main LLM Paths

### Generic path

If the router classifies the question as `generic`:

1. `GenericAgent` performs vector retrieval through `VectorClient`
2. it formats the retrieved chunks as reference context
3. it asks Azure OpenAI for a final answer
4. it resolves source file names or URLs through `source_link_registry.py`
5. it returns:
   - `content`
   - optional `sources`

This path is mostly retrieval-augmented answering without building-session state.

### Building-specific path

If the router classifies the question as `building_specific`, it delegates to `BuildingAgent`.

`BuildingAgent` is the richest flow in the system.

It builds a LangGraph pipeline using `src/agents/building_flow_graph.py`.

The building flow has these major stages:

1. `understand_context`
   - parse intent from the latest user message
   - detect address
   - merge prior metadata and identifiers
   - preserve prior intent during address-only follow-ups
2. `route_after_ambiguity`
   - if the request is ambiguous and there is no usable address/filter, ask for clarification
   - if a SQL-capable intent exists but the address is missing, ask for the building address
3. `maintain_history`
   - keeps the conversation state intact before fan-out
4. `decision_router`
   - maps intent labels to actual agent nodes
5. agent execution
   - `generic_sql_agent`
   - `specialized_sql_agent`
   - `vector_db_agent`
6. `wait_for_replies`
   - barrier that checks whether all required agent branches finished
7. `aggregator`
   - merges structured outputs and diagnostic metadata
8. `llm_summarizer`
   - turns aggregated results into the final user-facing answer
9. session-state persistence
   - saves the full resulting graph state back into Redis under `session:{thread_id}`

#### Generic SQL agent

The generic SQL path uses `SQL_Mapper_Layer` and `SQLClient`.

This path mainly talks to the ODEN API.

It can:

- fetch by address
- fetch by supported single filter
- fetch by building UUID
- infer some field-level requests such as energy class or heated area

#### Specialized SQL agent

The specialized SQL path uses `SpecializedSQLLayer`.

This path:

1. loads database schema information from `src/config/schema.json`
2. asks a model to produce exactly one SQL statement
3. executes that SQL through `src.database.hammarby_data.query_executor(sql)`
4. returns the resulting data or message

This is a more flexible but riskier path because the model is generating SQL dynamically.

#### Vector agent

The vector path uses `VectorClient`, which initializes `VectorDataBase` and `RetrievalText`.

This agent:

- queries the configured vector database
- returns retrieved snippets and their sources
- passes those sources upward so the final assistant response can expose clickable references

## 7. End-to-End Runtime Sequence

The normal live chat path across both services is:

1. The user submits a message in the frontend.
2. The frontend emits `send_message(message, session_id, session_id_int)` over Socket.IO.
3. `message-service` appends the user message to Redis list `thread:{session_id}:messages`.
4. `message-service` inserts the same user message into PostgreSQL.
5. `message-service` publishes a `thread_events` event for the thread.
6. `llm-service` receives the event and reads the full Redis thread.
7. `llm-service` routes the latest user turn through the router and agents.
8. `llm-service` appends the assistant payload back into the same Redis thread.
9. `message-service` polling sees the assistant reply appear in Redis.
10. `message-service` inserts the assistant text into PostgreSQL.
11. `message-service` emits `session_updated` and `answer_message`.
12. The frontend renders the assistant message, sources, report button, and rating UI.

## 8. What Is Durable vs Ephemeral

This is one of the most important architectural points in the current system.

### Durable in PostgreSQL

Persisted reliably:

- users
- sessions
- user messages
- assistant message text
- ratings

### Ephemeral or Redis-only

Not durably preserved in the same way:

- `sources`
- `classification`
- `agent_answered`
- `downloadable_report`
- expert handoff flags
- building-agent session state
- thread metadata

This means a message can be durable as plain text while the richer assistant metadata is not.

### Reconnect consequence

When the user reconnects, `message-service` rebuilds Redis from PostgreSQL messages.
That rebuild restores:

- message text
- role
- timestamp
- rating metadata

It does not restore most richer assistant payload fields such as:

- `sources`
- `downloadable_report`
- `classification`
- building-agent metadata

So some assistant features are effectively "live Redis features" rather than "historically durable features".

## 9. Important Implementation Gaps and Risks

The system is functional, but there are several rough edges worth knowing up front.

### Socket authentication is weaker than REST authentication

REST endpoints use JWT validation.
Socket events currently trust client-provided values such as:

- `user_id`
- `session_id`
- `session_id_int`

There is no matching JWT enforcement in the Socket.IO event path.
That means the chat transport is less protected than the REST transport.

### Disconnect cleanup uses the wrong Redis key

In `events/handlers.py`, `disconnect()` deletes `session_id` directly instead of deleting `thread:{session_id}:messages`.

Effect:

- the code says the thread was deleted
- the actual Redis message list is likely left behind

### Timeout fallback writes to the wrong Redis key

In the `send_message()` timeout path, the timeout message is pushed to `session_id` instead of `thread:{session_id}:messages`.

Effect:

- timeout fallback is probably not stored where the rest of the system expects thread messages

### Polling cadence is coarse

`send_message()` sleeps for 10 seconds inside its reply polling loop, even though the comment says 0.5 seconds.

Effect:

- replies may feel delayed or batchy even when the LLM finished faster

### Cluster route appears incomplete

`AgentRouter` contains a `cluster` branch and calls `self.cluster.handle_cluster_query(...)`.
The current `ClusterAgent` implementation only defines `run(...)`.

Effect:

- if the router ever returns `cluster`, this path is likely broken

### The current Docker path does not use all code in the repo

There is older or legacy code that is present but not part of the main runtime path:

- `message-service/app/web/*` is a Flask/Celery stack
- `message-service/tasks.py` is tied to that Flask stack
- `llm-service/rag_redis_pub_sub.py` and `main_retrieval_generation.py` reflect an older Redis worker path

The active runtime path is the FastAPI + Socket.IO service and the `generation.py` Redis worker.

### Ratings table initialization is duplicated

`shared/db/init.sql` creates `ratings`, and `message-service` also calls `ensure_rating_table_exists()` at startup.

Effect:

- harmless redundancy
- useful to know when tracing initialization

## 10. Best Files to Read First

If you want to understand the running system quickly, read these files in this order:

1. `infra/docker-compose.dev.yml`
2. `message-service/main.py`
3. `message-service/socket_manager/app.py`
4. `message-service/events/handlers.py`
5. `message-service/service/entrypoints.py`
6. `message-service/service/database.py`
7. `llm-service/generation.py`
8. `llm-service/src/redis/redis_manager.py`
9. `llm-service/src/pipeline/agent_router.py`
10. `llm-service/src/agents/building_flow_graph.py`

## 11. Final Mental Model

The cleanest way to think about SPARA today is:

- `message-service` is the orchestrating gateway and durable recorder
- `llm-service` is the asynchronous intelligence worker
- PostgreSQL is the durable conversation archive
- Redis is the live working memory, message bus, and cross-service glue

The most important architectural nuance is that the user-visible chat text is durable, but a meaningful portion of the richer assistant behavior still lives only in Redis-backed runtime state.
