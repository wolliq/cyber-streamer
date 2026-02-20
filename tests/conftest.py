"""Test configuration and setup."""

import os

# Set environment variables for testing before any other modules are imported
os.environ["KAFKA_SASL_AUTH_ENABLED"] = "False"
os.environ["KAFKA_BROKERS"] = "localhost:9092"
