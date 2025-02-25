# Automated Commit Testing & Deployment System

A fully automated system for fetching code from a remote system (backend.im), testing commits in isolated Kubernetes environments, and deploying successful builds to production.

## 📌 Overview

This system integrates GitHub Actions, WebSockets, and Kubernetes to streamline CI/CD workflows:

1. **Code Push:** The system (acting as backend.im) pushes code to GitHub.
2. **Pipeline Trigger:** A GitHub Actions workflow triggers on every push to the `main` branch.
3. **Client Activation:** The workflow runs `client.py`, which communicates with the **orchestration app** running on port `8080` on an Ubuntu server.
4. **Test Execution:** The orchestration app deploys the test environment inside the `test-environment` namespace of the `backend-im` Kubernetes cluster.
5. **Feedback Loop:**
   - If **tests fail**, a commit message is generated to notify the system.
   - If **tests pass**, the code is deployed to production and a WebSocket message confirms the deployment.


⚙️ Workflow Breakdown
- Step 1: Code Push & GitHub Actions Trigger
Code is pushed to the main branch.
GitHub Actions pipeline starts, running client.py.
- Step 2: Client Communicates with Orchestration App
client.py sends a WebSocket request to orchestration app running on port 8080.
The orchestration app starts a Kubernetes test pod.
- Step 3: Running Tests in Kubernetes
The orchestration app launches a test pod in the test-environment namespace.
The test pod clones the repository and runs tests.
Test results are sent back via WebSockets.
- Step 4: Deployment Decision
    - If tests fail, a commit message is created stating "Test failed".
    - If tests pass, the orchestration app:
Deploys the code to the prod-env namespace.
Sends a WebSocket message: "Production deployment successful".

🛠 Prerequisites
Kubernetes Cluster (backend-im cluster)
GitHub Actions configured
Ubuntu Server with WebSocket-enabled orchestration app running
Python 3.9+ and required dependencies.

🚀 Quick Start

1️⃣ Clone the Repository
git clone https://github.com/your-username/backend-im-infra.git
cd backend-im-infra

2️⃣ Configure GitHub Actions
Add your Kubernetes cluster credentials to GitHub Secrets.
Ensure pipeline.yml is correctly configured for test execution.

3️⃣ Deploy the Orchestration App
Run the orchestration app on an Ubuntu server:
python scripts/orchestration_app.py

4️⃣ Push Code to GitHub
git add .
git commit -m "New feature"
git push origin main
This triggers the pipeline, which starts the testing process.
🔥 Troubleshooting

1️⃣ Test Pod Crashing (CrashLoopBackOff)
kubectl logs <test-pod-name> -n test-environment
Ensure dependencies are installed correctly inside the pod.

2️⃣ WebSocket Connection Issues
curl -I http://localhost:8080/health
Verify the orchestration app is running on the correct port.

3️⃣ Deployment Not Happening
kubectl get pods -n prod-env
Check if production pods are running successfully.

🎯 Future Improvements
✅ Automated rollback for failed production deployments.
✅ Integration with monitoring tools like Prometheus/Grafana.
✅ Support for additional backend frameworks.
