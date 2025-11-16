# start.ps1
$container = docker ps -a --filter "name=^/mongo-hackathon$" --format "{{.Names}}"

if ($container -eq "mongo-hackathon") {
    Write-Host "Restarting MongoDB..."
    docker start mongo-hackathon | Out-Null
} else {
    Write-Host "Creating MongoDB container..."
    docker run -d --name mongo-hackathon -p 27017:27017 `
        -e MONGO_INITDB_ROOT_USERNAME=hackathon `
        -e MONGO_INITDB_ROOT_PASSWORD=password123 `
        -e MONGO_INITDB_DATABASE=hackathon_db `
        mongo:4.4 | Out-Null
}

# Wait for Mongo to accept connections (retry loop)
Write-Host "Waiting for MongoDB to be ready..."
$maxTries = 30
$tries = 0
while ($true) {
    $res = docker exec mongo-hackathon mongo --quiet --eval "db.adminCommand('ping')" 2>$null
    if ($res -and $res -match '"ok"') {
        Write-Host "MongoDB is ready."
        break
    }
    Start-Sleep -Seconds 2
    $tries++
    if ($tries -ge $maxTries) {
        Write-Host "Timed out waiting for MongoDB." -ForegroundColor Red
        exit 1
    }
}

# Create app user in hackathon_db (idempotent attempt)
Write-Host "Creating application user 'hackathon' in hackathon_db (if not exists)..."
$createUserCmd = @"
var db = db.getSiblingDB('hackathon_db');
try {
  db.createUser({
    user: 'hackathon',
    pwd: 'password123',
    roles: [{ role: 'readWrite', db: 'hackathon_db' }]
  });
  print('user-created');
} catch(e) {
  // ignore if already exists
  print('user-exists-or-error:' + e);
}
"@
docker exec -i mongo-hackathon mongo --quiet --eval $createUserCmd | Out-Null

# Activate venv and install requirements
.\venv\Scripts\Activate.ps1
pip install -q --upgrade pip
pip install -q --upgrade -r requirements.txt

Write-Host "Running ETL..."
python main.py "data/raw/combined.txt" "test_source"

Write-Host "Starting API at http://localhost:8000"
Start-Process "http://localhost:8000"
uvicorn api.api:app --host 0.0.0.0 --port 8000
