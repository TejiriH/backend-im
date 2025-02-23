import asyncio
import json
import websockets
import os

async def send_commit():
    try:
        # Get the commit ID from GitHub Actions environment variable
        commit_id = os.getenv("GITHUB_SHA")
        if not commit_id:
            print("❌ No commit ID provided. Ensure GITHUB_SHA is available in your GitHub Actions environment.")
            return

        websocket_url = "ws://51.21.131.153:8080/ws"
        async with websockets.connect(websocket_url) as websocket:
            commit_data = json.dumps({"commit_id": commit_id})
            await websocket.send(commit_data)
            print(f"🚀 Sent commit ID: {commit_id} to {websocket_url}")

            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"🔍 Response from WebSocket: {data}")

                    # Exit when final status is received
                    if data.get("status") in ["success", "failure", "error"]:
                        break
                except websockets.exceptions.ConnectionClosedOK:
                    print("✅ Connection closed by the server.")
                    break

    except Exception as e:
        print(f"❌ Error in WebSocket connection: {e}")

if __name__ == "__main__":
    asyncio.run(send_commit())



