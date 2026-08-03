import os
from datetime import datetime

import requests
from influx_writer import writer as db

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Aria
ARIA_HOST = os.getenv("ARIA_HOST")
ARIA_USER = os.getenv("ARIA_USER")
ARIA_AUTH_SOURCE = os.environ.get("ARIA_AUTH_SOURCE", "local")
ARIA_PASSWD = os.getenv("ARIA_PASSWD")
ARIA_RESOURCE_ID1 = os.getenv("ARIA_RESOURCE_ID1")
ARIA_RESOURCE_ID2 = os.getenv("ARIA_RESOURCE_ID2")
MAP_ID1 = os.getenv("MAP_ID1")
MAP_ID2 = os.getenv("MAP_ID2")


class AriaCollector:
# Voici un exemple de ce que doit ressembler la variable auth
# auth = { "username": "user", "authSource": "local", "password": "password" }

    def __init__(self, host: str, auth: dict):
        self.base_url = f"https://{host}/suite-api/api"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        self.session.verify = False
        self.token = self.__get_token(auth)
        self.session.headers.update({"Authorization": f"OpsToken {self.token}"})
        self.end = int(datetime.now().timestamp() * 1000)
        self.begin = self.end - (30 * 24 * 60 * 60 * 1000)
        self.names_map = { ARIA_RESOURCE_ID1 : MAP_ID1, ARIA_RESOURCE_ID2 : MAP_ID2 }
        self.lines = [] # list of influxDB line

    def __get_token(self, payload: dict):
        url = f"{self.base_url}/auth/token/acquire"
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            print("Successfully authenticated to Aria")
            return response.json()["token"]
        except requests.exceptions.RequestException as e:
            print("❌ No authentication token obtained. Aborting...")
            raise SystemExit(e)

    def __influx_line_protocol(self, data_json, measurement: str):
        lp = []

        if not data_json or "values" not in data_json:
            return lp

        for resource in data_json["values"]:
            resource_id = resource.get("resourceId")
            resource_name = str(self.names_map.get(resource_id, resource_id) if self.names_map else resource_id)

            stat_list = resource.get("stat-list", {}).get("stat", [])

            for stat in stat_list:
                raw_key = stat.get("statKey")
                metric_name = raw_key["key"].replace("|", "_")

                timestamps = stat.get("timestamps", [])
                data_points = stat.get("data", [])

                for ts, val in zip(timestamps, data_points):
                    if val is None or val == 0:
                        continue

                    tag_resource = resource_name.replace(" ", "\\ ")

                    timestamp_ns = int(ts) * 1000000

                    line = f"{measurement},datacenter={tag_resource} {metric_name}={val} {timestamp_ns}"
                    lp.append(line)

        return lp

    def get_total_vms(self):
        url = f"{self.base_url}/resources/stats/latest"
        payload = {
            "resourceId": [ARIA_RESOURCE_ID1, ARIA_RESOURCE_ID2],
            "statKey": [
                "summary|total_number_vms"
            ],
        }
        try:
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                print(f" Error {response.status_code}:", response.text)
            response.raise_for_status()
            lp = self.__influx_line_protocol(response.json(), "vm_inventory")
            self.lines.extend(lp)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def aria_vmop(self):
        url = f"{self.base_url}/resources/stats/query"
        payload = {
            "resourceId": [ARIA_RESOURCE_ID1, ARIA_RESOURCE_ID2],
            "statKey": [
                "vmop|inventoryChange|numCreate_latest",
                "vmop|inventoryChange|numDestroy_latest"
            ],
            "begin": self.begin,
            "end": self.end,
            "rollUpType": "SUM",
            "intervalType": "DAYS",
            "intervalQuantifier": 1
        }
        try:
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                print(f" Error {response.status_code}:", response.text)
            response.raise_for_status()
            lp = self.__influx_line_protocol(response.json(), "vm_inventory")
            self.lines.extend(lp)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def aria_cpu_mem(self):
        url = f"{self.base_url}/resources/stats/query"
        payload = {
            "resourceId": [ARIA_RESOURCE_ID1, ARIA_RESOURCE_ID2],
            "statKey": [
                "cpu|workload",
                "mem|workload",
            ],
            "begin": self.begin,
            "end": self.end,
            "rollUpType": "AVG",
            "intervalType": "DAYS",
            "intervalQuantifier": 1
        }
        try:
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                print(f" Error {response.status_code}:", response.text)
            response.raise_for_status()
            lp = self.__influx_line_protocol(response.json(), "system_metrics")
            self.lines.extend(lp)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def collect(self):
        print("📊 Collecting data...")
        self.get_total_vms()
        self.aria_vmop()
        self.aria_cpu_mem()


if __name__ == "__main__":
    print(f"--- Start collecting from VMware Aria ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

    auth = { "username": ARIA_USER, "authSource": ARIA_AUTH_SOURCE, "password": ARIA_PASSWD }
    try:
        aria = AriaCollector(str(ARIA_HOST), auth)
        aria.collect()
    except BaseException as e:
        print(f"❌ Error: {e}")
        exit()

    print("Writing to InfluxDB...")
    for line in aria.lines:
        db.write_line(line)

    db.close()
    print("--- End ---")
