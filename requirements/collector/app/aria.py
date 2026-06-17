import os
from datetime import datetime

import requests
from influx_writer import writer

# Aria
ARIA_HOST = os.environ.get("ARIA_HOST")
ARIA_USER = os.environ.get("ARIA_USER")
ARIA_PASSWD = os.environ.get("ARIA_PASSWD")


def get_aria_token():
    url = f"https://{ARIA_HOST}/suite-api/api/auth/token/acquire"
    data = {"username": ARIA_USER, "password": ARIA_PASSWD}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()["token"]
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def collect_aria_data(token):
    url = f"https://{ARIA_HOST}/suite-api/api/resources/<OBJECT_UUID>/stats/latest"
    headers = {
        "Accept": "application/json",
        "Authorization": f"vRealizeOpsToken {token}",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


if __name__ == "__main__":
    print(
        f"--- Start collecting from VMware Aria ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---"
    )
    token = get_aria_token()
    if token:
        print("📊 Collecting data...")
        data = collect_aria_data(token)

        if data:
            print("Writing to InfluxDB...")
            writer.write_point("aria", {"object_uuid": OBJECT_UUID}, data)
            writer.close()
        else:
            print("❌ No data collected.")

        print("--- End ---")
    else:
        print("❌ No authentication token obtained. Aborting...")
