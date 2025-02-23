import asyncio
import json
from fastapi import FastAPI, WebSocket
from kubernetes import client, config
import time
import random
import string

app = FastAPI()

# Load Kubernetes config
def load_kube_config():
    try:
        config.load_kube_config()
        print("✅ Loaded kubeconfig correctly")
    except Exception:
        config.load_incluster_config()
        print("✅ Loaded in-cluster kubeconfig")

load_kube_config()
api_client = client.ApiClient()
v1 = client.CoreV1Api(api_client)

# Kubernetes namespaces
NAMESPACE_TEST = "test-environment"
NAMESPACE_PROD = "prod-env"

# Generate unique pod name
def generate_unique_pod_name(commit_id):
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test-runner-{commit_id}-{timestamp}-{random_str}"

# Function to deploy a production pod
def deploy_production(commit_id):
    pod_name = f"production-pod-{commit_id}"
    print(f"🚀 Deploying production pod {pod_name} in namespace {NAMESPACE_PROD}...")

    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(name=pod_name, namespace=NAMESPACE_PROD),
        spec=client.V1PodSpec(
            restart_policy="Always",
            containers=[client.V1Container(
                name="production-container",
                image="python:3.9",
                command=["/bin/sh", "-c"],
                args=[
                    "ls -la /workspace && rm -rf /workspace && "  # Delete existing directory before cloning
                    "apt update && apt install -y git && "
                    "git clone https://github.com/TejiriH/backend-im.git /workspace && "
                    "cd /workspace && pip install -r requirements.txt && python helloworld.py"
                ],
                volume_mounts=[client.V1VolumeMount(name="workspace-volume", mount_path="/workspace")]
            )],
            volumes=[client.V1Volume(name="workspace-volume", empty_dir=client.V1EmptyDirVolumeSource())]
        )
    )

    # Create the pod
    v1.create_namespaced_pod(namespace=NAMESPACE_PROD, body=pod)
    print(f"✅ Production pod {pod_name} deployed, waiting for it to start...")

    # Wait for pod to reach "Running" state or fail
    for _ in range(30):  # Wait up to 30 seconds
        pod_status = v1.read_namespaced_pod_status(pod_name, NAMESPACE_PROD)
        phase = pod_status.status.phase
        if phase == "Running":
            print(f"✅ Production pod {pod_name} is running!")
            return {"status": "success", "commit_id": commit_id, "pod_name": pod_name}
        elif phase in ["Failed", "Unknown"]:
            print(f"❌ Production pod {pod_name} failed to start!")
            return {"status": "failed", "commit_id": commit_id, "pod_name": pod_name}
        time.sleep(2)  # Wait 2 seconds before checking again

    print(f"⚠️ Production pod {pod_name} is stuck, check logs manually.")
    return {"status": "timeout", "commit_id": commit_id, "pod_name": pod_name}

# Function to handle test runs
async def test_runner(websocket: WebSocket):
    try:
        data = await websocket.receive_json()
        commit_id = data["commit_id"]
        pod_name = generate_unique_pod_name(commit_id)

        print(f"🔍 Received commit {commit_id}. Starting test pod {pod_name}...")

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
                        "cd /workspace && pip install -r requirements.txt && pytest test.py"
                    ],
                    volume_mounts=[client.V1VolumeMount(name="workspace-volume", mount_path="/workspace")]
                )],
                volumes=[client.V1Volume(name="workspace-volume", empty_dir=client.V1EmptyDirVolumeSource())]
            )
        )

        v1.create_namespaced_pod(namespace=NAMESPACE_TEST, body=pod)
        await websocket.send_json({"status": "started", "commit_id": commit_id, "pod_name": pod_name})

        # Wait for pod completion
        while True:
            pod_status = v1.read_namespaced_pod_status(name=pod_name, namespace=NAMESPACE_TEST).status.phase
            if pod_status in ["Succeeded", "Failed"]:
                break
            await asyncio.sleep(2)

        result = "success" if pod_status == "Succeeded" else "failure"
        await websocket.send_json({"status": result, "commit_id": commit_id, "pod_name": pod_name})

        if result == "success":
            prod_response = deploy_production(commit_id)
            await websocket.send_json(prod_response)  # Send production pod status to client

    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
        print(f"❌ Error: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await test_runner(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        await websocket.close()  # Ensure the WebSocket is properly closed






