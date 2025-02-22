import asyncio
import json
import websockets
from fastapi import FastAPI
from kubernetes import client, config
from fastapi import WebSocket
import time
import random
import string

app = FastAPI()

# Load Kubernetes config
config.load_kube_config()

NAMESPACE = "test-environment"

# Function to generate a unique pod name
def generate_unique_pod_name(commit_id):
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test-runner-{commit_id}-{timestamp}-{random_str}"

async def test_runner(websocket):
    try:
        # Receive commit data from the WebSocket client
        message = await websocket.receive_text()
        data = json.loads(message)
        commit_id = data["commit_id"]

        # Generate a unique pod name
        pod_name = generate_unique_pod_name(commit_id)

        print(f"Received commit {commit_id}. Starting test pod with name {pod_name}...")

        # Create a Kubernetes test pod
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name, namespace=NAMESPACE),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[client.V1Container(
                    name="test-container",
                    image="python:3.9",
                    command=["/bin/sh", "-c"],
                    args=[f"apt update && apt install -y git && "
                          f"git clone https://github.com/TejiriH/backend-im.git /workspace && "
                          f"cd /workspace && pip install -r requirements.txt && pytest helloworld.py"],
                    volume_mounts=[client.V1VolumeMount(name="workspace-volume", mount_path="/workspace")]
                )],
                volumes=[client.V1Volume(name="workspace-volume", empty_dir=client.V1EmptyDirVolumeSource())]
            )
        )

        # Deploy pod to Kubernetes
        v1 = client.CoreV1Api()
        v1.create_namespaced_pod(namespace=NAMESPACE, body=pod)

        # Send initial status to the client
        await websocket.send_json({"status": "started", "commit_id": commit_id, "pod_name": pod_name})

        # Monitor pod status and logs
        while True:
            # Check the pod's current status
            pod_status = v1.read_namespaced_pod_status(name=pod_name, namespace=NAMESPACE)
            if pod_status.status.phase == "Running":
                # If the pod is running, start monitoring logs
                logs = v1.read_namespaced_pod_log(name=pod_name, namespace=NAMESPACE)
                await websocket.send_json({"status": "running", "logs": logs})
            elif pod_status.status.phase in ["Succeeded", "Failed"]:
                # If the pod has finished, exit the loop
                break

            await asyncio.sleep(2)  # Check the status every 2 seconds

        # Send final result
        result = "success" if pod_status.status.phase == "Succeeded" else "failure"
        await websocket.send_json({"status": result, "commit_id": commit_id, "pod_name": pod_name})

    except Exception as e:
        # Send error message as a JSON string (text message)
        error_message = {"status": "error", "message": str(e)}
        await websocket.send_json(error_message)  # Sending JSON string
        print(f"Error: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await test_runner(websocket)



