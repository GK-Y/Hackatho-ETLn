## !!This code will only run on c drive of windows under folder name Hackathon !!

### 1. Project & Directory Setup

| **Action**              | **Windows (PowerShell)**                                                  | **WSL (Bash)**                                                          |
| ----------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Clone Repo**          | `cd C:\`<br><br>  <br><br>`git clone https://your-repo-url.git Hackathon` | `cd ~`<br><br>  <br><br>`git clone https://your-repo-url.git Hackathon` |
| **Navigate to Backend** | `cd C:\Hackathon\hackathon_etl_v2`                                        | `cd ~/Hackathon/hackathon_etl_v2`                                       |

---

### 2. MongoDB Container & User

These commands assume **Docker Desktop is running** on Windows/WSL.

| **Action**               | **Windows (PowerShell) / WSL (Bash)**                                                                                                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pull & Run Container** | `docker pull mongo:6.0`<br><br>  <br><br>`docker run -d --name mongo-hackathon -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=adminpass mongo:6.0`                                   |
| **Wait (Required)**      | `Start-Sleep -Seconds 5` (PowerShell)<br><br>  <br><br>`sleep 5` (Bash)                                                                                                                                                |
| **Create DB User**       | `docker exec -i mongo-hackathon mongosh --eval "db.getSiblingDB('admin').createUser({user:'hackathon', pwd:'password123', roles:[{role:'readWrite', db:'hackathon_db'},{role:'userAdminAnyDatabase', db:'admin'}]});"` |

---

### 3. Backend (Python) Setup

The `.env` file must be created _first_ using the full absolute paths.

| **Action**                 | **Windows (PowerShell) (Replace C:\...)**                                                                                                                                                                                     | **WSL (Bash) (Replace ~/...)**                                                                                                                                                                                                                                     |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Create `.env`**          | `@"MONGO_URI=mongodb://hackathon:password123@localhost:27017/?authSource=admin`<br><br>  <br><br>`DATABASE_NAME=hackathon_db`<br><br>  <br><br>`TEST_FILES_DIR=C:\Hackathon\etl_test_files"@ \| Out-File -Encoding utf8 .env` | `cat > .env <<'EOF'`<br><br>  <br><br>`MONGO_URI=mongodb://hackathon:password123@localhost:27017/?authSource=admin`<br><br>  <br><br>`DATABASE_NAME=hackathon_db`<br><br>  <br><br>`TEST_FILES_DIR=/home/youruser/Hackathon/etl_test_files`<br><br>  <br><br>`EOF` |
| **Create & Activate Venv** | `python -m venv .venv`<br><br>  <br><br>`.\.venv\Scripts\Activate.ps1`                                                                                                                                                        | `python3 -m venv .venv`<br><br>  <br><br>`source .venv/bin/activate`                                                                                                                                                                                               |
| **Install Deps**           | `pip install -r requirements.txt`                                                                                                                                                                                             | `pip install -r requirements.txt`                                                                                                                                                                                                                                  |
| **Run Server**             | `python -m uvicorn api.api:app --reload --host 127.0.0.1 --port 8000`                                                                                                                                                         | `python -m uvicorn api.api:app --reload --host 127.0.0.1 --port 8000`                                                                                                                                                                                              |

---

### 4. Frontend (Node) Setup (New Terminal/Tab)

| **Action**        | **Windows (PowerShell)**                     | **WSL (Bash)**                               |
| ----------------- | -------------------------------------------- | -------------------------------------------- |
| **Navigate**      | `cd C:\Hackathon\frontend`                   | `cd ~/Hackathon/frontend`                    |
| **Install & Run** | `npm install`<br><br>  <br><br>`npm run dev` | `npm install`<br><br>  <br><br>`npm run dev` |

---
Here is a concise section for the prerequisites of your setup guide.

---

## Requirements

Ensure your environment meets these minimum specifications before starting the setup process.

### Software Prerequisites

| **Tool**           | **Minimum Version** | **Reason**                                                                    |
| ------------------ | ------------------- | ----------------------------------------------------------------------------- |
| **Docker Desktop** | Latest Stable       | Required to run the MongoDB database container. Must be running.              |
| **Python**         | 3.10+               | Required for the backend API and setting up the virtual environment (`venv`). |
| **Node.js**        | 18+ (LTS)           | Required for the frontend application and dependency management (`npm`).      |
| **Git**            | Latest Stable       | Required for cloning the repository.                                          |

### Configuration Notes

- **Docker:** Ensure Docker is running and available on your system, especially within your **WSL** instance if you are primarily using that environment.
    
- **PATH:** Both the `python` and `node` executables (and their associated `npm`/`pip`) must be accessible in your system's `PATH` from the terminal you are working in.
