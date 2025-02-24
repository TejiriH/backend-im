import asyncio  # Ensure this import is present
import json
import websockets
import os

async def send_commit():
    try:
        commit_id = os.getenv("GITHUB_SHA")
        if not commit_id:
            print("❌ No commit ID provided. Ensure GITHUB_SHA is available in your GitHub Actions environment.")
            return

        websocket_url = "ws://51.20.89.231:8080/ws"
        async with websockets.connect(websocket_url) as websocket:
            commit_data = json.dumps({"commit_id": commit_id})
            await websocket.send(commit_data)
            print(f"🚀 Sent commit ID: {commit_id} to {websocket_url}")

            test_passed = False  # Track test phase completion

            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"🔍 Response from WebSocket: {data}")

                    if data.get("status") in ["success", "failure", "error"]:
                        if data["status"] == "success":
                            test_passed = True  # Mark that test passed
                        else:
                            break  # If test failed, stop listening

                    # If test passed, keep listening for production messages
                    if test_passed and data.get("pod_name", "").startswith("production-pod-"):
                        break  # Exit after production deployment message

                except websockets.exceptions.ConnectionClosedOK:
                    print("✅ Connection closed by the server.")
                    break

    except Exception as e:
        print(f"❌ Error in WebSocket connection: {e}")

if __name__ == "__main__":
    asyncio.run(send_commit())





