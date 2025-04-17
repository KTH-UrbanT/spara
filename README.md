# SPARA

This is a cumulative repository for SPARA - chatbot for energy efficiency in buildings. It includes the following components:

- **frontend** - React JS based client
- **message-service** - Python Fast API-based web server
- **llm-service** - Python langchain-based language service

To fetch the project codebase to the local machine, the following should be done:

```
git clone git@github.com:KTH-UrbanT/spara.git
git clone --recursive git@github.com:KTH-UrbanT/spara.git
```

## Composing the Docker

### Development

Build and run the development environment:

```
docker compose -f infra/docker-compose.dev.yml up --build
```

### Production

Build and run the production environment:

```
docker compose -f infra/docker-compose.prod.yml up --build -d
```

## Accessing the services

### locally

- ReactJS client - `http://localhost:5173`
- FastAPI server - `http://localhost:8000`

### remote

- ReactJS client - `http://<server-ip>:5173`
- FastAPI server - `http://<server-ip>:8000`
