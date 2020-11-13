#!/usr/bin/env python3

import asyncio
import json
import logging
import websockets
import random

logging.basicConfig(level=logging.INFO)
sessions = {}

async def app(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            session_id = data.get("session_id")
            logging.info(f"action:{action} session_id:{session_id}")
            sess = sessions.get(session_id)
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
                await websocket.send(json.dumps(sess["entries"]))
            elif action == "upsert_entry":
                entry = data.get("entry")
                entry_id = entry.get("id")
                sess["entries"][entry_id] = entry
                message = json.dumps({"upserted_entry": entry}) # Inform all connected users about the new entry
                await asyncio.wait([user.send(message) for user in sess["users"]])
            else:
                logging.error("unsupported event: {}", data)
    except websockets.exceptions.ConnectionClosedError as e:
        logging.error(f"User disconnected: {e}")
    finally:
        for session_id, sess in sessions.items():
            if websocket in sess["users"]:
                sess["users"].remove(websocket)
                if len(sess["users"]) > 0:
                    message = json.dumps({"user_count": len(sess["users"])}) # Inform all connected users about the disconnected user
                    await asyncio.wait([user.send(message) for user in sess["users"]])


start_server = websockets.serve(app, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()