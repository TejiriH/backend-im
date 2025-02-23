import asyncio
import json
import websockets

commit_id = "26926471"
websocket_url = "ws://51.21.131.153:8080/ws"

async def send_commit():
    try:
        async with websockets.connect(websocket_url) as websocket:
            commit_data = json.dumps({"commit_id": commit_id})
            await websocket.send(commit_data)

            while True:
                response = await websocket.recv()
                print(f"Response from WebSocket: {response}")
                response_data = json.loads(response)
                
                if response_data.get("status") in ["success", "failure", "error"]:
                    break

            await websocket.close()  # Explicitly close connection

    except Exception as e:
        print(f"❌ Error in WebSocket connection: {e}")

if __name__ == "__main__":
    asyncio.run(send_commit())





