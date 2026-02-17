#!/bin/bash
set -e

echo "============================================"
echo "      STARTING E2E TEST FLOW"
echo "============================================"

# 1. Start Infrastructure
echo "[1/5] Starting Infrastructure (Kafka, Redis)..."
# Cleanup any existing containers to avoid conflicts
docker rm -f kafka redis || true
export ADV_HOST=localhost
docker compose up -d kafka redis

# Function to check if a port is open
wait_for_port() {
  local host=$1
  local port=$2
  local name=$3
  echo "Waiting for $name ($host:$port)..."
  for i in {1..30}; do
    if nc -z "$host" "$port"; then
      echo "$name is up!"
      return 0
    fi
    sleep 1
  done
  echo "$name failed to start."
  exit 1
}


wait_for_port localhost 9092 "Kafka"
wait_for_port localhost 6379 "Redis"

# Function to wait for Kafka to be ready (topics listable)
wait_for_kafka_ready() {
  echo "Waiting for Kafka to be ready..."
  for i in {1..30}; do
    if docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
      echo "Kafka is ready!"
      return 0
    fi
    sleep 1
  done
  echo "Kafka failed to become ready."
  exit 1
}

wait_for_kafka_ready

# 2. Add Topics (Idempotent)
echo "[2/5] Creating Kafka Topics..."
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic user-events --partitions 1 --if-not-exists
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic login-events --partitions 1 --if-not-exists
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic buy-events --partitions 1 --if-not-exists

# 3. Start App in Background
echo "[3/5] Starting FastAPI App..."
# Use a log file to capture output
LOG_FILE="e2e_app.log"
KAFKA_BROKERS=localhost:9092 KAFKA_SASL_AUTH_ENABLED=False uv run uvicorn app.main:app --app-dir src --port 8888 > "$LOG_FILE" 2>&1 &
APP_PID=$!
echo "App started with PID $APP_PID. Logs in $LOG_FILE"

# Wait for App to be healthy
echo "Waiting for App health check..."
for i in {1..30}; do
  if curl -s http://localhost:8888/health | grep "healthy" > /dev/null; then
    echo "App is healthy!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "App failed to start. Logs:"
    cat "$LOG_FILE"
    kill $APP_PID
    exit 1
  fi
  sleep 1
done

# 4. Run Generator
echo "[4/5] Running Traffic Generator (Bot Attack)..."
# Just running the bot scenario
KAFKA_BROKERS=localhost:9092 KAFKA_SASL_AUTH_ENABLED=False uv run python src/app/generator.py --mode bot

# Sleep a bit to let the app process events
echo "Waiting for processing..."
sleep 5

# 5. Verification (Grep Logs)
echo "[5/5] Verifying Fraud Detection..."
if grep -q "Fraud Detected" "$LOG_FILE"; then
  echo "✅ SUCCESS: Fraud Detected in logs."
  grep "Fraud Detected" "$LOG_FILE"
else
  echo "❌ FAILURE: No Fraud Detected in logs."
  echo "Last 50 lines of logs:"
  tail -n 50 "$LOG_FILE"
  # Don't exit with error yet, let cleanup happen, but mark failure
  TEST_FAILED=true
fi

# Cleanup
echo "============================================"
echo "      CLEANING UP"
echo "============================================"
kill $APP_PID || true
# Optional: Stop docker
# docker compose down

if [ "$TEST_FAILED" = true ]; then
  exit 1
fi

echo "E2E Test Passed!"
