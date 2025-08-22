"""Debug and visualize GoodWe API integration.

This script uses the demo GoodWe API (SEMS portal) to validate
credentials and fetch inverter data. It can help diagnose
communication issues by printing raw responses from the API.

Credentials are read from environment variables or command-line
arguments:

- ``SEMS_ACCOUNT``
- ``SEMS_PASSWORD``
- ``SEMS_REGION`` (optional, defaults to ``us``)

Example usage:

```bash
python goodwe_debug.py --inverter-id 5010KETU229W6177 --column Cbattery1 \
  --date "2025-08-12 00:21:01"
```

If only credentials are provided, the script performs a login and
reports success. Provide ``--inverter-id`` and ``--date`` to query
inverter data by column and display the JSON response.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import pprint
from typing import Any, Dict, Literal

import requests

Region = Literal["us", "eu"]
BASE: Dict[Region, str] = {
    "us": "https://us.semsportal.com",
    "eu": "https://eu.semsportal.com",
}


def _initial_token() -> str:
    """Generate the pre-login token required by the SEMS portal."""
    original = {
        "uid": "",
        "timestamp": 0,
        "token": "",
        "client": "web",
        "version": "",
        "language": "en",
    }
    b = json.dumps(original).encode("utf-8")
    return base64.b64encode(b).decode("utf-8")


def crosslogin(account: str, pwd: str, region: Region = "us") -> str:
    """Authenticate with the GoodWe API and return an access token."""
    url = f"{BASE[region]}/api/v2/common/crosslogin"
    headers = {"Token": _initial_token(), "Content-Type": "application/json", "Accept": "*/*"}
    payload = {
        "account": account,
        "pwd": pwd,
        "agreement_agreement": 0,
        "is_local": False,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    js = response.json()
    if "data" not in js or js.get("code") not in (0, 1, 200):
        raise RuntimeError(f"Login failed: {js}")
    data_to_string = json.dumps(js["data"])
    token = base64.b64encode(data_to_string.encode("utf-8")).decode("utf-8")
    return token


def get_inverter_data_by_column(
    token: str, inv_id: str, column: str, date: str, region: Region = "eu"
) -> Dict[str, Any]:
    """Fetch inverter data for a specific column and timestamp."""
    url = f"{BASE[region]}/api/PowerStationMonitor/GetInverterDataByColumn"
    headers = {"Token": token, "Content-Type": "application/json", "Accept": "*/*"}
    payload = {"date": date, "column": column, "id": inv_id}
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug GoodWe API integration")
    parser.add_argument("--account", default=os.getenv("SEMS_ACCOUNT"))
    parser.add_argument("--password", default=os.getenv("SEMS_PASSWORD"))
    parser.add_argument("--region", default=os.getenv("SEMS_REGION", "us"))
    parser.add_argument("--inverter-id", dest="inv_id")
    parser.add_argument("--column", default="Cbattery1")
    parser.add_argument("--date", help="YYYY-MM-DD HH:MM:SS")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    missing = [name for name in ("account", "password") if not getattr(args, name)]
    if missing:
        raise SystemExit(f"Missing credentials: {', '.join(missing)}")

    try:
        token = crosslogin(args.account, args.password, args.region)
        print("Login successful.")
        if args.inv_id and args.date:
            data = get_inverter_data_by_column(token, args.inv_id, args.column, args.date, args.region)
            pprint.pprint(data)
        else:
            print("Token acquired. Provide --inverter-id and --date to query inverter data.")
    except Exception as exc:  # noqa: BLE001 - show raw exception for debugging
        print("Error during API call:", exc)


if __name__ == "__main__":
    main()
