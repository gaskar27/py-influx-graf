import os
from datetime import datetime
import requests
from influxdb_client_3 import Point
from influx_writer import writer as db
from utils import get_secrets

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DC_NAME = os.getenv("DC_NAME")
NAME = os.getenv("NAME")

class UnityCollector:
    def authenticate(self):
        response = self.session.get(f"{self.base_url}/types/loginSessionInfo/instances")
        if response.status_code == 200:
            self.token = response.headers.get("EMC-CSRF-TOKEN")
            self.session.headers.update({"EMC-CSRF-TOKEN": str(self.token)})
            return True
        return False

    def __init__(self, ip, username, password):
        self.base_url = f"https://{ip}/api"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = False
        self.session.headers.update({"X-EMC-REST-CLIENT": "true", "Accept": "application/json"})
        self.token = None
        self.points:list[Point] = [] # list of Point objects
        self.isAuthenticated = False
        if self.authenticate():
            self.isAuthenticated = True

    # def get_metrics(self, type, fields):
        # url = f"{self.base_url}/types/{type}/instances"
        # params = {"fields": fields}
        # response = self.session.get(url, params=params)
        # return response.json().get("entries", []) if response.json() else None

    def get_metrics(self, type, fields= None, filter=None):
        url = f"{self.base_url}/types/{type}/instances"

        params = {}
        if fields is not None:
            params["fields"] = fields
        if filter is not None:
            params["filter"] = filter

        response = self.session.get(url, params=params if params else None)

        if response.ok:
            data = response.json()
            return data.get("entries", []) if response.json() else None
        return None

    def __influx_point(self, response):
        if not response:
            return
        for item in response:
            content = item.get("content", {})
            name = content.get("name", "unknown")
            id_val = content.get("id", "unknown")
            point = (Point("unity_metrics").time(item["updated"])
                     .tag("name", name)
                     .tag("id", id_val)
                     .tag("datacenter", DC_NAME))
            for k, v in content.items():
                if k not in ["name", "id"]:
                    point.field(k, v)
            self.points.append(point)

    def __influx_point_sp(self, response):
        if not response:
            return
        for item in response:
            content = item.get("content", {})
            name = content.get("name", "unknown")
            id_val = content.get("id", "unknown")
            point = (Point("unity_metrics").time(item["updated"])
                     .tag("name", name)
                     .tag("id", id_val)
                     .tag("datacenter", DC_NAME))
            for k, v in content.items():
                if k == "values":
                    for ke, va in content[k].items():
                        point.field(ke, va)
                    continue
                if k == "timestamp":
                    point.time(v)
                    continue
                if k not in ["name", "id"]:
                    point.field(k, v)
            self.points.append(point)

    def get_storage_processor_metrics(self):
        params = "path eq \"sp.*.cpu.summary.utilization\""
        response = self.get_metrics("metricValue", filter=params)
        self.__influx_point_sp(response)

    def get_system_metrics(self):
        fields = "name,model,serialNumber"
        response = self.get_metrics("system", fields)
        self.__influx_point(response)

    def get_pool_metrics(self):
        fields = "name,sizeTotal,sizeUsed,sizeSubscribed"
        response = self.get_metrics("pool", fields)
        self.__influx_point(response)

    def get_luns_metrics(self):
        fields = "name,sizeAllocated,sizeTotal,pool"
        response = self.get_metrics("luns", fields)
        self.__influx_point(response)

    def get_filesystem_metrics(self):
        fields = "name,sizeAllocated,sizeTotal"
        response = self.get_metrics("filesystem", fields)
        self.__influx_point(response)

    def get_disk_metrics(self):
        fields = "name,sizeAllocated,sizeTotal"
        response = self.get_metrics("disk", fields)
        self.__influx_point(response)

    def get_all_metrics(self):
        self.get_storage_processor_metrics()
        self.get_system_metrics()
        self.get_pool_metrics()
        self.get_luns_metrics()
        self.get_filesystem_metrics()
        self.get_disk_metrics()

if __name__ == "__main__":
    s = get_secrets(NAME)
    print(f"--- Start collecting from DELL Unity ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

    unity = UnityCollector(s.get("UNITY_HOST"), s.get("UNITY_USER"), s.get("UNITY_PASSWD"))

    if not unity.isAuthenticated:
        print("Unable to Authenticate")
        exit()

    unity.get_all_metrics()

    print("Writing to InfluxDB...")
    for point in unity.points:
        db.write_point(point)

    db.close()
    print("--- End ---")
