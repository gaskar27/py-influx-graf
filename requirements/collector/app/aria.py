import os
from datetime import datetime

import requests
from influx_writer import writer

# Aria
ARIA_HOST = os.environ.get("ARIA_HOST")
ARIA_USER = os.environ.get("ARIA_USER")
ARIA_PASSWD = os.environ.get("ARIA_PASSWD")
ARIA_RESOURCE_ID1 = os.environ.get("ARIA_RESOURCE_ID1")
ARIA_RESOURCE_ID2 = os.environ.get("ARIA_RESOURCE_ID2")


def get_aria_token():
    url = f"https://{ARIA_HOST}/suite-api/api/auth/token/acquire"
    data = {"username": ARIA_USER, "authSource": "local", "password": ARIA_PASSWD}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()["token"]
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def collect_aria_data(token):
    url = f"https://{ARIA_HOST}/suite-api/api/resources/stats/latest"
    headers = {
        "Accept": "application/json",
        "Authorization": f"OpsToken {token}",
    }
    data = {
        "resourceId": [ARIA_RESOURCE_ID1, ARIA_RESOURCE_ID2],
        "statKey": ["summary|total_number_vms", "summary|number_running_vms"],
    }
    try:
        response = requests.post(url, headers=headers, json=data)
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
            writer.write_records(data)
            writer.close()
        else:
            print("❌ No data collected.")

        print("--- End ---")
    else:
        print("❌ No authentication token obtained. Aborting...")
