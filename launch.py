#!/usr/bin/env python3
"""
NiPlex Harness — public entrypoint.
HidenCloud / Pterodactyl / local entrypoint.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)


def ensure_deps():
    req = ROOT / "requirements.txt"
    if not req.exists():
        return
    marker = ROOT / ".deps_installed"
    req_hash = hashlib.sha256(req.read_bytes()).hexdigest()
    if marker.exists() and marker.read_text().strip() == req_hash:
        return  # requirements.txt unchanged since the last install
    print("[launch] Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req), "--quiet"])
    marker.write_text(req_hash)
    print("[launch] Dependencies ready.")


def main():
    ensure_deps()
    env_file = ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    gateway = os.getenv("GATEWAY", "discord").lower().strip()
    print(f"[launch] Starting NiPlex Harness — gateway={gateway}")

    if gateway == "telegram":
        from gateway.telegram import run
        run()
    elif gateway == "discord":
        from gateway.discord import run
        run()
    else:
        print(f"Unknown GATEWAY={gateway}. Use telegram or discord.")
        sys.exit(1)


if __name__ == "__main__":
    main()
