"""Standalone smoke test for the Owlet cloud connection.

Exercises the exact same call sequence the integration itself makes
(OwletAPI.authenticate -> validate_authentication -> get_devices,
then Sock.update_properties per device) but runs standalone, with no
Home Assistant install required. Useful for confirming your account
credentials work and that pyowletapi can still fetch and parse live
sock data before wiring the integration into HA.

Requires Python 3.10+ (pyowletapi's own minimum).

Usage:
    python -m venv .venv
    .venv\\Scripts\\pip install pyowletapi==2025.4.1 aiohttp
    .venv\\Scripts\\python scripts/smoke_test.py --region europe --email you@example.com
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import sys

import aiohttp
from pyowletapi.api import OwletAPI
from pyowletapi.exceptions import OwletError
from pyowletapi.sock import Sock

# Mirrors custom_components/owlet/const.py SUPPORTED_VERSIONS
SUPPORTED_VERSIONS = [2, 3]


async def run(region: str, email: str, password: str) -> int:
    """Authenticate, list devices, and print parsed properties for each."""
    async with aiohttp.ClientSession() as session:
        api = OwletAPI(region=region, user=email, password=password, session=session)

        print("Authenticating...")
        await api.authenticate()

        print("Validating credentials...")
        await api.validate_authentication()

        print("Fetching devices...")
        devices = await api.get_devices(SUPPORTED_VERSIONS)
        device_list = devices.get("response", [])

        if not device_list:
            print("No devices returned - check the account has a sock registered "
                  "and the --region matches where the account is registered.")
            return 1

        for entry in device_list:
            info = entry["device"]
            print(f"\nDevice: {info.get('product_name')} ({info.get('dsn')})")

            sock = Sock(api, info)
            properties = await sock.update_properties()
            print("Parsed properties:")
            print(json.dumps(properties, indent=2, default=str))

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=["europe", "world"], required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Owlet password: ")

    try:
        return asyncio.run(run(args.region, args.email, password))
    except OwletError as err:
        print(f"Owlet API error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
