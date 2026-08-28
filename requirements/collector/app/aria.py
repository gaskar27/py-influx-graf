import os
from datetime import datetime

import requests
from influxdb_client_3 import Point

from influx_writer import writer as db
from utils import get_secrets

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Aria
ARIA_RESOURCE_ID1 = str(os.getenv("ARIA_RESOURCE_ID1"))
ARIA_RESOURCE_ID2 = str(os.getenv("ARIA_RESOURCE_ID2"))
MAP_ID1 = os.getenv("MAP_ID1")
MAP_ID2 = os.getenv("MAP_ID2")


class AriaCollector:

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
        self.points = [] # list of influxDB point

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

    def __get_vm_destroy_date(self, id:str):
        url = f"{self.base_url}/resources/{id}/stats/latest"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                print(f" Error {response.status_code}:", response.text)
            response.raise_for_status()
            data = response.json()
            values = data.get("values", [])
            if not values:
                return None

            stats = values[0].get("stat-list", {}).get("stat", [])
            if not stats:
                return None

            timestamps = stats[0].get("timestamps", [])
            if not timestamps:
                return None
            return timestamps[0] # the result is in millisecond

        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def __convert_to_influx_point(self, data, instance_id):
        resource_name = str(self.names_map.get(instance_id, instance_id) if self.names_map else instance_id)
        for item in data:
            vm_name = item.get("resourceKey", {}).get("name")
            created_at = item.get("creationTime")
            is_deleted = False
            vm_id = item.get("identifier")
            destroyed_at = None
            for state in item.get("resourceStatusStates", []):
                if state.get("resourceState") == "NOT_EXISTING":
                    is_deleted = True
                    break

            if is_deleted:
                destroyed_at = self.__get_vm_destroy_date(vm_id)
            point = (Point("vm_lifecycle").time(created_at).tag("datacenter", resource_name)
                     .tag("name", vm_name).tag("id", vm_id).field("is_deleted", is_deleted)
                     .field("created_at", created_at)).field("destroyed_at", destroyed_at)
            self.points.append(point)

    def get_total_vms(self):
        url = f"{self.base_url}/resources/stats/latest?resourceId={ARIA_RESOURCE_ID1}&resourceId={ARIA_RESOURCE_ID2}&statKey=summary|total_number_vms"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                print(f" Error {response.status_code}:", response.text)
            response.raise_for_status()
            lp = self.__influx_line_protocol(response.json(), "vm_inventory")
            self.lines.extend(lp)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def get_vms_resource_stat(self, adapter_instance_id: str):
        url = f"{self.base_url}/resources/query"
        payload = {
            "resourceKind" : [ "VirtualMachine" ],
            "adapterInstanceId" : [ adapter_instance_id ],
        }
        try:
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                print(f" Error {response.status_code}:", response.text)
            response.raise_for_status()
            if response.json():
                self.__convert_to_influx_point(response.json().get("resourceList", []), adapter_instance_id)
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
        self.get_vms_resource_stat(ARIA_RESOURCE_ID1)
        self.get_vms_resource_stat(ARIA_RESOURCE_ID2)


if __name__ == "__main__":
    s = get_secrets("aria_s")
    print(f"--- Start collecting from VMware Aria ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

    auth = { "username": s.get("ARIA_USER"), "authSource": s.get("ARIA_AUTH_SOURCE"), "password": s.get("ARIA_PASSWD")}
    try:
        aria = AriaCollector(s.get("ARIA_HOST"), auth)
        aria.collect()
    except BaseException as e:
        print(f"❌ Error: {e}")
        exit()

    print("Writing to InfluxDB...")
    for line in aria.lines:
        db.write_line(line)

    for point in aria.points:
        db.write_point(point)

    db.close()
    print("--- End ---")
