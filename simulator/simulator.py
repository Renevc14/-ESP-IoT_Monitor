# IoT Device Simulator
# Authenticates as operator, registers devices, sends sensor readings
# 20% chance of out-of-range value to trigger alerts
import os
import time
import random
import httpx

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
EMAIL = os.getenv("OPERATOR_EMAIL", "operator@iot.local")
PASSWORD = os.getenv("OPERATOR_PASSWORD", "Operator1234!")
NUM_DEVICES = int(os.getenv("NUM_DEVICES", "3"))
NUM_READINGS = int(os.getenv("NUM_READINGS", "10"))


def main():
    print(f"[simulator] Starting — {NUM_DEVICES} devices × {NUM_READINGS} readings")
    # Implementation added in Commit 9
    print("[simulator] Placeholder — full implementation in commit 9")


if __name__ == "__main__":
    main()
