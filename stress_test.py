#!/usr/bin/env python3

import asyncio
import websockets
import json
import random
import time
import pandas as pd

URI = "wss://api-proxy.auckland-cer.cloud.edu.au/dynamic_network_graph"
#URI = "ws://api-proxy.auckland-cer.cloud.edu.au:6789"
#URI = "ws://localhost:6789"
SESSION_ID = "STRESS_TEST"
MAX_CLIENTS = 1000

async def test():
    start = time.time()
    async with websockets.connect(URI) as websocket:
        ttc = time.time() - start
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
        tts = time.time() - start
        try:
            while True:
                await asyncio.wait_for(websocket.recv(), 0)
        except asyncio.exceptions.TimeoutError:
            pass
        ttr = time.time() - start
        await websocket.close()
        tte = time.time() - start
        return {"ttc": ttc, "tts": tts, "ttr": ttr, "tte": tte}

async def run_n_tests(n):
    results = await asyncio.gather(*[test() for i in range(n)])
    df = pd.DataFrame(results)
    return df

print("n_clients,mttc,mtts,mttr,mtte,wall_time")
for n_clients in range(10, MAX_CLIENTS, 100):
    start = time.time()
    df = asyncio.run(run_n_tests(n_clients))
    print(f"{len(df)},{','.join(str(x) for x in df.mean().values)},{time.time() - start}")