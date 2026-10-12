"""Small, serial Swedish smoke test over the deployed demo's normal chat path.

Uses one unique synthetic temporary account via the public registration/login
flow. Never sends handoff/report requests. Credentials and session tokens stay
in memory; output contains only numeric evaluation IDs and redacted answers.
Requires websocket-client and requests (not a browser usability test).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import uuid

import requests
import websocket

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_CASES = ["SV_01", "SV_02", "SV_07", "SV_09", "SV_17"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/pilot_sv/results/demo_smoke.jsonl")
    args = parser.parse_args()
    base = "https://demo.sparabot.com"
    email = f"spara-pilot-sv-{uuid.uuid4().hex[:12]}@example.com"
    http = requests.Session()
    http.headers["User-Agent"] = "SPARA-Swedish-Pilot-Smoke/1.0"
    # These endpoints, inspected in this repository, create an app account only;
    # they do not send verification or advisor email.
    response = http.post(base + "/user/register/temporary/", json={"email": email}, timeout=20)
    response.raise_for_status()
    user_id = response.json()["user_id"]
    response = http.post(base + "/user/login/temporary/", json={"temp_user_id": user_id}, timeout=20)
    response.raise_for_status()
    token = response.json()["access_token"]
    http.headers["Authorization"] = "Bearer " + token
    print(f"Synthetic test account created; user ID {user_id}. No email requested.", flush=True)
    cases = {row["case_id"]: row for line in (ROOT / "evaluation/data/swedish_pilot_cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip() for row in [json.loads(line)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output:
        for case_id in ALLOWED_CASES:
            case = cases[case_id]
            turns = case.get("turns") or [{"user": case["question"]}]
            ws = None
            session_id_int = None
            session_token = None
            try:
                ws = websocket.create_connection(
                    "wss://demo.sparabot.com/socket.io/?EIO=4&transport=websocket",
                    timeout=10, origin=base, header={"Authorization": "Bearer " + token},
                )
                opening = ws.recv()
                if not opening.startswith("0"):
                    raise RuntimeError("Unexpected Engine.IO opening packet")
                ws.send("40" + json.dumps({"user_id": user_id, "email": email, "session_id": None, "session_id_int": None, "token": token}))

                def receive_until(target, timeout=30):
                    deadline = time.monotonic() + timeout
                    while time.monotonic() < deadline:
                        ws.settimeout(min(10, max(0.1, deadline - time.monotonic())))
                        try:
                            packet = ws.recv()
                        except websocket.WebSocketTimeoutException:
                            continue
                        if not packet:
                            raise RuntimeError("Chat connection closed")
                        if packet == "2":
                            ws.send("3")
                        elif packet.startswith("40") and target == "connected":
                            return {}
                        elif packet.startswith("44"):
                            raise RuntimeError("Chat authentication rejected")
                        elif packet.startswith("42"):
                            event = json.loads(packet[2:])
                            if event[0] == "error_message":
                                raise RuntimeError("Chat returned an error event")
                            if event[0] == target:
                                return event[1]
                    raise TimeoutError(f"No {target} event within {timeout}s")

                receive_until("connected")
                ws.send("42" + json.dumps(["create_session", turns[0]["user"], user_id, email], ensure_ascii=False))
                session = receive_until("session_created")
                session_token, session_id_int = session["session_id"], session["session_id_int"]
                for index, turn in enumerate(turns):
                    started = time.monotonic()
                    ws.send("42" + json.dumps(["send_message", turn["user"], session_token, session_id_int], ensure_ascii=False))
                    result = receive_until("answer_message", timeout=125)
                    content = str(result.get("content", ""))
                    # Never persist the raw event, which contains session identifiers.
                    for value in [session_token, email, token]:
                        content = content.replace(value, "[redacted]")
                    row = dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                               target=base, test_type="deployed_chat_smoke", case_id=case_id,
                               turn_index=index, evaluation_id=f"spara-session-{session_id_int}",
                               user_message=turn["user"], assistant_content=content,
                               latency_seconds=round(time.monotonic() - started, 2),
                               request_completed=True, semantic_review="pending")
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
                    output.flush()
                    print(f"{case_id} turn {index}: reply received in {row['latency_seconds']}s", flush=True)
            except Exception as exc:
                # Avoid exceptions containing auth headers or raw server payloads.
                row = dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(), target=base,
                           test_type="deployed_chat_smoke", case_id=case_id,
                           request_completed=False, error_type=type(exc).__name__,
                           semantic_review="not_assessable")
                output.write(json.dumps(row) + "\n")
                output.flush()
                print(f"{case_id}: {type(exc).__name__}; stopping smoke run.", flush=True)
                return 1
            finally:
                if ws:
                    ws.close()
                if session_id_int is not None:
                    try:
                        response = http.patch(base + f"/session/{session_id_int}/active/", params={"is_active": "false"}, timeout=15)
                        response.raise_for_status()
                    except requests.RequestException:
                        print(f"Cleanup pending: deactivate own test session {session_id_int}.", flush=True)
    print(f"Smoke completed; responses still require review: {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
