#!/usr/bin/env just --justfile
[private]
default:
  @just --list

# install the dependencies for the project
install:
	uv sync

# format code with ruff
format:
	uv run ruff format .

# test that the formatting is correct using ruff
format-test:
	uv run ruff format --check .

# run pre-commit checks
precommit:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .
	uv run pylint src/app/

# run the tests
test:
	KAFKA_SASL_USER=dummy KAFKA_SASL_PASSWORD=dummy PYTHONPATH=src uv run python -m pytest tests/

# Run Kafka in a Docker container
kafka-server:
    docker run -p 2181:2181 \
      -p 3030:3030 \
      -p 8081-8083:8081-8083 \
      -p 9581-9585:9581-9585 \
      -p 9092:9092 \
      -e ADV_HOST=127.0.0.1 \
      lensesio/fast-data-dev:latest

# Add new topics to Kafka
kafka-add-topics:
    kafka-topics --bootstrap-server localhost:9092 --create --topic user-events --partitions 1 || true
    kafka-topics --bootstrap-server localhost:9092 --create --topic order-events --partitions 1 || true
    kafka-topics --bootstrap-server localhost:9092 --create --topic article-events --partitions 1 || true
    kafka-topics --bootstrap-server localhost:9092 --create --topic login-events --partitions 1 || true
    kafka-topics --bootstrap-server localhost:9092 --create --topic buy-events --partitions 1 || true
    kafka-topics --bootstrap-server localhost:9092 --create --topic scroll-events --partitions 1 || true

# Produce test samples (requires samples in tests/samples/fraud/)
kafka-produce-user:
    echo '{"user_id": "u1", "email": "test@example.com", "phone": "+1234567890", "address": "123 Main St", "registration_date": "2023-01-01T10:00:00Z"}' | kafka-console-producer --bootstrap-server localhost:9092 --topic user-events

kafka-produce-login:
    echo '{"user_id": "u1", "timestamp": "2023-10-27T10:00:00Z", "ip_address": "192.168.1.1", "device_id": "d1", "success": true}' | kafka-console-producer --bootstrap-server localhost:9092 --topic login-events

kafka-produce-buy:
    echo '{"user_id": "u1", "order_id": "o1", "timestamp": "2023-10-27T10:05:00Z", "payment_method": "credit_card"}' | kafka-console-producer --bootstrap-server localhost:9092 --topic buy-events

kafka-produce-scroll:
    echo '{"user_id": "u1", "article_id": "a1", "timestamp": "2023-10-27T10:02:00Z", "percentage": 0.8, "duration_seconds": 120.5}' | kafka-console-producer --bootstrap-server localhost:9092 --topic scroll-events

# Run the FastAPI app locally
run-locally:
	uv run uvicorn app.main:app --app-dir src --port 8888 --reload

# Use the local installed binary to check consumer activity
kafka-consume-fraud-scores:
    # Note: Gold tables are Parquet/Delta, not Kafka topics, but checking logs is good
    echo "Check application logs for fraud scores"

build:
    docker build --no-cache -t fkl-streamer .
run:
    docker run --env-file .envrc_docker -p 8000:8000 fkl-streamer
run-it:
    docker run -it fkl-streamer /bin/sh
run-docker-compose:
    docker compose up --build
log-fastapi:
    docker logs fkl-streamer


k8s-apply:
    kubectl apply -f deploy/deployment.yaml
    kubectl apply -f deploy/service.yaml
k8s-port-forward:
    kubectl port-forward svc/fkl-streamer-app-service 8080:80
