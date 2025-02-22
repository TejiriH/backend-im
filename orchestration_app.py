import asyncio
import json
import websockets
from fastapi import FastAPI, WebSocket
from kubernetes import client, config
import time
import random
import string

app = FastAPI()

# Load Kubernetes config
config.load_kube_config()

NAMESPACE_TEST = "test-environment"
NAMESPACE_PROD = "prod-env"

# Function to generate a unique pod name
def generate_unique_pod_name(commit_id):
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test-runner-{commit_id}-{timestamp}-{random_str}"

def deploy_production(commit_id):
    v1 = client.CoreV1Api()
    pod_name = f"production-pod-{commit_id}"
    
    print(f"Deploying production pod {pod_name} in namespace {NAMESPACE_PROD}...")

    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(name=pod_name, namespace=NAMESPACE_PROD),
        spec=client.V1PodSpec(
            restart_policy="Always",
            containers=[client.V1Container(
                name="production-container",
                image="python:3.9",
                command=["/bin/sh", "-c"],
                args=[
                    "apt update && apt install -y git && "
                    "git clone https://github.com/TejiriH/backend-im.git /workspace && "
                    "cd /workspace && pip install -r requirements.txt && python app.py"
                ],
                volume_mounts=[client.V1VolumeMount(name="workspace-volume", mount_path="/workspace")]
            )],
            volumes=[client.V1Volume(name="workspace-volume", empty_dir=client.V1EmptyDirVolumeSource())]
        )
    )

    v1.create_namespaced_pod(namespace=NAMESPACE_PROD, body=pod)
    print(f"Production pod {pod_name} deployed successfully!")

async def test_runner(websocket):
    try:
        message = await websocket.receive_text()
        data = json.loads(message)
        commit_id = data["commit_id"]
        pod_name = generate_unique_pod_name(commit_id)

        print(f"Received commit {commit_id}. Starting test pod {pod_name}...")

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name, namespace=NAMESPACE_TEST),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[client.V1Container(
                    name="test-container",
                    image="python:3.9",
                    command=["/bin/sh", "-c"],
                    args=[
                        "apt update && apt install -y git && "
                        "git clone https://github.com/TejiriH/backend-im.git /workspace && "
                        "cd /workspace && pip install -r requirements.txt && pytest helloworld.py"
                    ],
                    volume_mounts=[client.V1VolumeMount(name="workspace-volume", mount_path="/workspace")]
                )],
                volumes=[client.V1Volume(name="workspace-volume", empty_dir=client.V1EmptyDirVolumeSource())]
            )
        )

        v1 = client.CoreV1Api()
        v1.create_namespaced_pod(namespace=NAMESPACE_TEST, body=pod)
        await websocket.send_json({"status": "started", "commit_id": commit_id, "pod_name": pod_name})

        while True:
            pod_status = v1.read_namespaced_pod_status(name=pod_name, namespace=NAMESPACE_TEST)
            if pod_status.status.phase == "Running":
                logs = v1.read_namespaced_pod_log(name=pod_name, namespace=NAMESPACE_TEST)
                await websocket.send_json({"status": "running", "logs": logs})
            elif pod_status.status.phase in ["Succeeded", "Failed"]:
                break
            await asyncio.sleep(2)

        result = "success" if pod_status.status.phase == "Succeeded" else "failure"
        await websocket.send_json({"status": result, "commit_id": commit_id, "pod_name": pod_name})
        
        if result == "success":
            deploy_production(commit_id)

    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
        print(f"Error: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await test_runner(websocket)




