#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:6789"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"action": "create_session"}))
        response = await websocket.recv()
        print(response)
        session_id = json.loads(response)["session_id"]
        #session_id = 3026
        await websocket.send(json.dumps({
            "action": "connect",
            "session_id": session_id
        }))
        await websocket.send(json.dumps({
            "session_id": session_id,
            "action": "upsert_entry",
            "entry": {
                "id": 2,
                "donor": "a",
                "resourceType": "$",
                "recipient": "c"
            }
        }))
        async for message in websocket:
            print(message)

asyncio.get_event_loop().run_until_complete(test())