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
	uv run pylint app/

# run the tests
test:
	uv run pytest -s tests/

# Run Kafka in a Docker container
kafka-server:
    docker run -p 2181:2181 \
      -p 3030:3030 \
      -p 8081-8083:8081-8083 \
      -p 9581-9585:9581-9585 \
      -p 9092:9092 \
      -e ADV_HOST=127.0.0.1 \
      lensesio/fast-data-dev:latest

# Add a new topic to Kafka
kafka-add-topics:
    kafka-topics --bootstrap-server localhost:9092 --create --topic media-radio-test --partitions 1

# Produce media channel radio test sample
kafka-produce-media-radio:
    jq -rc . tests/samples/media_channel_radio.json | kafka-console-producer --bootstrap-server localhost:9092 --topic media-radio-test
kafka-produce-media-radio-10:
    for i in {1..10}; do just kafka-produce-media-radio; done

# Produce media channel tv test sample
kafka-produce-media-tv:
    jq -rc . tests/samples/media_channel_tv.json | kafka-console-producer --bootstrap-server localhost:9092 --topic media-tv-test
kafka-produce-media-tv-10:
    for i in {1..10}; do just kafka-produce-media-tv; done

# Produce sale test sample
kafka-produce-sale:
    jq -rc . tests/samples/sale.json | kafka-console-producer --bootstrap-server localhost:9092 --topic sale-test
kafka-produce-sale-10:
    for i in {1..10}; do just kafka-produce-sale; done

# Run the FastAPI app locally
run-locally:
	uv run uvicorn app.main:app --port 8888 --reload

# Use the local installed binary to check consumer activity
kafka-consume-media-radio-test:
    kafka-console-consumer --bootstrap-server localhost:9092 --topic media-radio-test
kafka-consume-media-tv-test:
    kafka-console-consumer --bootstrap-server localhost:9092 --topic media-tv-test
kafka-consume-sale-test:
    kafka-console-consumer --bootstrap-server localhost:9092 --topic sale-test

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