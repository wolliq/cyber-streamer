#!/bin/bash
set -e

echo "============================================"
echo "      STARTING E2E TEST FLOW"
echo "============================================"

# 1. Start Infrastructure
echo "[1/5] Starting Infrastructure (Kafka, Redis)..."
# Cleanup any existing containers to avoid conflicts
docker rm -f kafka redis cyber-streamer || true
# Ensure we don't export ADV_HOST=localhost, letting it default to kafka (internal) or user env
unset ADV_HOST
docker compose up -d kafka redis

# Function to check if a port is open
wait_for_port() {
  local host=$1
  local port=$2
  local service=$3
  echo "Waiting for $service ($host:$port)..."
  for i in {1..30}; do
    if nc -z "$host" "$port"; then
      echo "Connection to $host port $port [tcp/test] succeeded!"
      echo "$service is up!"
      return 0
    fi
    sleep 1
  done
  echo "$service failed to come up."
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

# Pre-pull micro model for faster testing
echo "[1.5/5] Pre-pulling Micro LLM Model (qwen2.5:0.5b)..."
curl -X POST http://localhost:11434/api/pull -d '{"name": "qwen2.5:0.5b"}'

# 2. Add Topics (Idempotent)
echo "[2/5] Creating Kafka Topics..."
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic user-events --partitions 1 --if-not-exists
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic login-events --partitions 1 --if-not-exists
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic buy-events --partitions 1 --if-not-exists

# 3. Run FastAPI App (Docker)
echo "[3/5] Starting FastAPI App (Docker)..."
# Build first to ensure latest code
# Ensure .envrc exists for Docker build (copy from template if missing)
if [ ! -f .envrc ]; then
  cp .envrc_docker .envrc
fi
docker compose build fastapi
OLLAMA_MODEL="qwen2.5:0.5b" docker compose up -d fastapi

echo "Waiting for App health check..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health | grep "healthy" > /dev/null; then
    echo "App is healthy!"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "App failed to start."
    docker logs cyber-streamer
    exit 1
  fi
  sleep 1
done

# 4. Run Generator (Docker)
echo "[4/5] Running Traffic Generator (Bot Attack)..."
# Run generator inside the network. We use the fastapi image which has the code.
# We override KAFKA_BROKERS to point to the kafka service name.
docker compose run --rm \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_SASL_AUTH_ENABLED=False \
  -e OLLAMA_MODEL="qwen2.5:0.5b" \
  fastapi \
  uv run python -m app.generator --mode bot

# Wait for processing and Verify Output
echo "[5/5] Verifying Fraud Detection..."
echo "Waiting for processing (up to 120s)..."

FRAUD_DETECTED=false
for i in {1..24}; do
  if docker logs cyber-streamer 2>&1 | grep -q "Fraud Detected"; then
    FRAUD_DETECTED=true
    break
  fi
  sleep 5
done

if [ "$FRAUD_DETECTED" = true ]; then
  echo "✅ SUCCESS: Fraud Detected in logs."
  docker logs cyber-streamer 2>&1 | grep "Fraud Detected"
else
  echo "❌ FAILURE: Fraud NOT Detected."
  echo "Last 50 lines of app logs:"
  docker logs --tail 50 cyber-streamer
  exit 1
fi

echo "============================================"
echo "      CLEANING UP"
echo "============================================"

echo "E2E Test Passed!"
