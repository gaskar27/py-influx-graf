import os
from datetime import datetime

import requests
# from influx_writer import writer

# Aria
ARIA_HOST = os.environ.get("ARIA_HOST", None)
ARIA_USER = os.environ.get("ARIA_USER", None)
ARIA_AUTH_SOURCE = os.environ.get("ARIA_AUTH_SOURCE", "local")
ARIA_PASSWD = os.environ.get("ARIA_PASSWD", None)
ARIA_RESOURCE_ID1 = os.environ.get("ARIA_RESOURCE_ID1", None)
ARIA_RESOURCE_ID2 = os.environ.get("ARIA_RESOURCE_ID2", None)


class AriaCollector:
    def __get_token(self):
        url = f"https://{ARIA_HOST}/suite-api/api/auth/token/acquire"
        payload = {
            "username": ARIA_USER,
            "authSource": ARIA_AUTH_SOURCE,
            "password": ARIA_PASSWD,
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["token"]
        except requests.exceptions.RequestException as e:
            print("❌ No authentication token obtained. Aborting...")
            raise SystemExit(e)

    def __init__(self):
        self.token = self.__get_token()
        self.end = int(datetime.now().timestamp() * 1000)
        self.begin = self.end - (30 * 24 * 60 * 60 * 1000)
        self.names_map = { ARIA_RESOURCE_ID1 : "vSphere ANALAKELY", ARIA_RESOURCE_ID2 : "vSphere GALAXY" }
        self.lines = []

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
        url = f"https://{ARIA_HOST}/suite-api/api/resources/stats/latest"
        headers = {
            "Accept": "application/json",
            "Authorization": f"OpsToken {self.token}",
        }
        payload = {
            "resourceId": [ARIA_RESOURCE_ID1, ARIA_RESOURCE_ID2],
            "statKey": [
                "summary|total_number_vms"
            ],
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            lp = self.__influx_line_protocol(response.json(), "vm_inventory")
            self.lines.extend(lp)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def aria_vmop(self):
        url = f"https://{ARIA_HOST}/suite-api/api/resources/stats/query"
        headers = {
            "Accept": "application/json",
            "Authorization": f"OpsToken {self.token}",
        }
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
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            lp = self.__influx_line_protocol(response.json(), "vm_inventory")
            self.lines.extend(lp)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    def aria_cpu_mem(self):
        url = f"https://{ARIA_HOST}/suite-api/api/resources/stats/query"
        headers = {
            "Accept": "application/json",
            "Authorization": f"OpsToken {self.token}",
        }
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
            response = requests.post(url, headers=headers, json=payload)
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


aria = AriaCollector()

# if __name__ == "__main__":
    # print(
        # f"--- Start collecting from VMware Aria ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---"
    # )

    # token = get_aria_token()
    # if token:
        # data = aria_total_vms(token)

        # if data:
            # print("Writing to InfluxDB...")
            # writer.write_records(data)
            # writer.close()
        # else:
            # print("❌ No data collected.")

        # print("--- End ---")
