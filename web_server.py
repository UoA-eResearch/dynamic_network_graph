#!/usr/bin/env python3

import asyncio
import json
import logging
import websockets
import random
import signal
import sys

logging.basicConfig(level=logging.INFO)
try:
    with open("db.json", "r") as f:
        sessions = json.load(f)
        logging.info("loaded DB from file")
except Exception as e:
    logging.error(f"Error loading DB, starting fresh. {e}")
    sessions = {}

def save():
    logging.info("Saving")
    safe_sess = {sid: {"entries": sess["entries"]} for sid, sess in sessions.items()}
    with open("db.json", "w") as f:
        json.dump(safe_sess, f)

def receiveSignal(signalNumber, frame):
    logging.info("SIGTERM caught")
    save()
    sys.exit()

signal.signal(signal.SIGTERM, receiveSignal)

async def save_loop():
    while True:
        await asyncio.sleep(300)
        save()

async def app(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            session_id = data.get("session_id")
            logging.info(f"action:{action} session_id:{session_id}")
            sess = sessions.get(session_id)
            if session_id and not sess:
                sess = {
                    "entries": {},
                    "users": set([websocket]),
                }
                sessions[session_id] = sess
            if sess and not sess.get("users"):
                sess["users"] = set([websocket])
            if action == "create_session":
                session_id = random.randint(0, 9999)
                sessions[session_id] = {
                    "entries": {},
                    "users": set([websocket]),
                }
                await websocket.send(json.dumps({"session_id": session_id}))
            elif action == "connect":
                sess["users"].add(websocket)
                message = json.dumps({"user_count": len(sess["users"])}) # Inform all connected users about the newly connected user
                await asyncio.wait([user.send(message) for user in sess["users"]])
            elif action == "request_entries":
                await websocket.send(json.dumps({
                    "entries": sess["entries"]
                }))
            elif action == "upsert_entry":
                entry = data.get("entry")
                entry_id = entry.get("id")
                sess["entries"][entry_id] = entry
                message = json.dumps({"entries": [entry]}) # Inform all connected users about the new entry
                await asyncio.wait([user.send(message) for user in sess["users"]])
            else:
                logging.error("unsupported event: {}", data)
    except websockets.exceptions.ConnectionClosedError as e:
        logging.error(f"User disconnected: {e}")
    finally:
        for session_id, sess in sessions.items():
            if sess.get("users") and websocket in sess["users"]:
                sess["users"].remove(websocket)
                if len(sess["users"]) > 0:
                    message = json.dumps({"user_count": len(sess["users"])}) # Inform all connected users about the disconnected user
                    await asyncio.wait([user.send(message) for user in sess["users"]])


start_server = websockets.serve(app, "localhost", 6789)

try:
    asyncio.get_event_loop().run_until_complete(asyncio.wait([
        start_server,
        save_loop()
    ]))
except Exception as e:
    logging.error(e)
    save()