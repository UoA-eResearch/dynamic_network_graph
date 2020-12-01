#!/usr/bin/env python3

import asyncio
import websockets
import json
import random
import time

URI = "wss://api-proxy.auckland-cer.cloud.edu.au/dynamic_network_graph"
#URI = "ws://api-proxy.auckland-cer.cloud.edu.au:6789"
#URI = "ws://localhost:6789"
SESSION_ID = "STRESS_TEST"
connections = []

async def read_all(websocket):
    try:
        while True:
            await asyncio.wait_for(websocket.recv(), 0)
    except:
        return

async def test(i):
    start = time.time()
    websocket = await websockets.connect(URI)
    connections.append(websocket)
    await websocket.send(json.dumps({
        "action": "connect",
        "session_id": SESSION_ID
    }))
    await websocket.send(json.dumps({
        "session_id": SESSION_ID,
        "action": "upsert_entry",
        "entry": {
            "id": random.randint(0, 100),
            "donor": random.randint(0, 100),
            "resourceType": "$",
            "recipient": random.randint(0, 100)
        }
    }))
    return time.time() - start

async def main():
    print("n_clients,t,wall_time")
    start = time.time()
    for i in range(1000):
        result = await test(i)
        print(f"{len(connections)},{result},{time.time() - start}")
        for ws in connections:
            await read_all(ws)

asyncio.get_event_loop().run_until_complete(main())