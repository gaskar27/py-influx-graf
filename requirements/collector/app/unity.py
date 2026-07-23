import os
import requests
from influxdb_client import Point

UNITY_HOST = os.getenv("UNITY_HOST")
UNITY_USER = os.getenv("UNITY_USER")
UNITY_PASSWD = os.getenv("UNITY_PASSWD")

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
        self.points = [] # list of Point objects
        self.isAuthenticated = False
        if self.authenticate():
            self.isAuthenticated = True

    def get_metrics(self, type, fields):
        url = f"{self.base_url}/types/{type}/instances"
        params = {"fields": fields}
        response = self.session.get(url, params=params)
        return response.json().get("entries", []) if response.json() else None

    def __influx_point(self, response):
        if not response:
            return
        for item in response:
            content = item.get("content", {})
            point = Point("unity_metrics").time(item["updated"]).tag("name", content["name"]).tag("id", content["id"])
            for k, v in content.items():
                if k not in ["name", "id"]:
                    point.field(k, v)
            self.points.append(point)

    def get_system_metrics(self):
        fields = "name,model,serialNumber,health"
        response = self.get_metrics("system", fields)
        self.__influx_point(response)

    def get_pool_metrics(self):
        fields = "name,sizeTotal,sizeUsed,sizeSubscribed,health"
        response = self.get_metrics("pool", fields)
        self.__influx_point(response)

    def get_luns_metrics(self):
        fields = "name,sizeAllocated,sizeTotal,health,pool"
        response = self.get_metrics("luns", fields)
        self.__influx_point(response)

    def get_filesystem_metrics(self):
        fields = "name,sizeAllocated,sizeTotal,health"
        response = self.get_metrics("filesystem", fields)
        self.__influx_point(response)

    def get_disk_metrics(self):
        fields = "name,sizeAllocated,sizeTotal,health"
        response = self.get_metrics("disk", fields)
        self.__influx_point(response)
