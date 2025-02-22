import asyncio
import json
import websockets
import os

async def send_commit():
    try:
        # Get the commit ID from the environment variable
        commit_id = os.getenv("COMMIT_ID")
        if not commit_id:
            print("No commit ID provided.")
            return

        async with websockets.connect("ws://51.20.124.73:8080/ws") as websocket:
            commit_data = json.dumps({"commit_id": commit_id})
            await websocket.send(commit_data)

            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print("Response:", data)

                    # Exit when result is received
                    if data.get("status") in ["success", "failure", "error"]:
                        break
                except websockets.exceptions.ConnectionClosedOK:
                    print("Connection closed by the server.")
                    break

    except Exception as e:
        print(f"Error: {e}")

asyncio.run(send_commit())


