"""
Event generator for E2E testing.

Generates synthetic events (User, Login, Order, Article, Buy, Scroll) and produces them to Kafka.
"""

import json
import random
import time
import logging
import argparse
from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Producer

from app.constants import (
    KAFKA_BROKERS,
    TOPIC_USER,
    TOPIC_LOGIN,
    TOPIC_BUY,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Mock Data
USER_IDS = [f"user_{i}" for i in range(1, 11)]
IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "8.8.8.8"]
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Python/3.12 aiohttp/3.9.1",  # Suspicious
]


def delivery_report(err, _msg):
    """Call once for each message produced to indicate delivery result."""
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        # logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
        pass


class EventGenerator:
    """Generate synthetic events and produce to Kafka."""

    def __init__(self, bootstrap_servers: str | None = KAFKA_BROKERS):
        """Initialize the event generator."""
        self.producer = Producer(
            {"bootstrap.servers": bootstrap_servers or "localhost:9092"}
        )

    def produce(self, topic: str, data: dict):
        """Produce a message to Kafka."""
        try:
            self.producer.produce(
                topic,
                key=data.get("user_id", str(uuid4())),
                value=json.dumps(data).encode("utf-8"),
                on_delivery=delivery_report,
            )
            self.producer.poll(0)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to produce message: %s", e)

    def flush(self):
        """Flush the producer."""
        self.producer.flush()

    def generate_user(self):
        """Generate a random user event."""
        user_id = random.choice(USER_IDS)
        return TOPIC_USER, {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "phone": "+1234567890",
            "address": "123 Main St",
            "registration_date": datetime.now(timezone.utc).isoformat(),
        }

    def generate_login(self, user_id=None, is_bot=False):
        """Generate a random login event."""
        uid = user_id or random.choice(USER_IDS)
        return TOPIC_LOGIN, {
            "user_id": uid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip_address": random.choice(IPS),
            "device_id": str(uuid4()),
            "user_agent": USER_AGENTS[3] if is_bot else random.choice(USER_AGENTS[:3]),
            "success": True,
        }

    def generate_buy(self, user_id=None):
        """Generate a random buy event."""
        uid = user_id or random.choice(USER_IDS)
        return TOPIC_BUY, {
            "user_id": uid,
            "order_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payment_method": "credit_card",
            "amount": round(random.uniform(10.0, 500.0), 2),
            "currency": "USD",
        }

    def run_scenario_bot_attack(self, target_user="user_victim"):
        """Simulate a bot attack: Rapid logins followed by buys."""
        logger.info("--- Starting BOT ATTACK Scenario on %s ---", target_user)

        # 1. Rapid Logins (High Frequency)
        for _ in range(15):
            topic, event = self.generate_login(user_id=target_user, is_bot=True)
            self.produce(topic, event)
            # Sleep tiny amount to ensure order but still be fast
            time.sleep(0.05)

        logger.info("Sent 15 login events for %s", target_user)

        # 2. Illogical Buy
        topic, event = self.generate_buy(user_id=target_user)
        self.produce(topic, event)
        logger.info("Sent buy event for %s", target_user)

        self.flush()

    def run_scenario_normal_traffic(self, count=20):
        """Simulate normal background traffic."""
        logger.info("--- Generating %s random normal events ---", count)
        for _ in range(count):
            choice = random.choice(["login", "buy", "user"])
            if choice == "login":
                t, e = self.generate_login()
            elif choice == "buy":
                t, e = self.generate_buy()
            else:
                t, e = self.generate_user()

            self.produce(t, e)
            time.sleep(random.uniform(0.1, 0.5))

        self.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Event Generator")
    parser.add_argument(
        "--mode",
        choices=["normal", "bot", "mixed"],
        default="mixed",
        help="Generation mode",
    )
    parser.add_argument("--count", type=int, default=10, help="Number of normal events")
    args = parser.parse_args()

    generator = EventGenerator()

    if args.mode == "normal":
        generator.run_scenario_normal_traffic(args.count)
    elif args.mode == "bot":
        generator.run_scenario_bot_attack()
    elif args.mode == "mixed":
        generator.run_scenario_normal_traffic(5)
        generator.run_scenario_bot_attack("bad_actor_1")
        generator.run_scenario_normal_traffic(5)
