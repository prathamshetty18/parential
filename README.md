# ROAVAI Parental Control Companion App & API

Parent companion backend service and Android application for **Wini**, the Cloud Tutor desktop robot.

---

## 🛠️ Step 1: Project Setup & Local Running Instructions (Windows PowerShell)

### 1. Configure Environment Variables
Copy `.env.example` to create your local `.env` file in Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

> **Note**: Do not commit your `.env` file to source control.

---

### 2. Start Services via Docker Compose
Run the following PowerShell command to build and launch both the PostgreSQL database (`db`) and FastAPI API service (`api`):

```powershell
docker compose up --build
```

To stop all services and tear down containers:

```powershell
docker compose down
```

---

### 3. Verify Health Endpoint
Once the containers are running, test the `/health` endpoint from PowerShell:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

Expected Output:
```json
{
  "status": "ok"
}
```

---

### 4. Run Pytest Suite Locally
To run the automated backend pytest test suite within virtual environment or docker container:

```powershell
# Run tests inside Docker container
docker compose exec api pytest

# Or run locally with python
cd backend
python -m pytest
```
