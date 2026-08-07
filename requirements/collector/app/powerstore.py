import os
import requests
from datetime import datetime
from influxdb_client_3 import Point
from influx_writer import writer as db

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

POWERSTORE_HOST = os.getenv("POWERSTORE_HOST")
POWERSTORE_USER = os.getenv("POWERSTORE_USER")
POWERSTORE_PASSWD = os.getenv("POWERSTORE_PASSWD")
DC_NAME = os.getenv("DC_NAME")

class PowerStoreCollector:
    def authenticate(self):
        response = self.session.get(f"{self.base_url}/login_session")
        if response.status_code == 200:
            self.token = response.headers.get("DELL-EMC-TOKEN")
            self.session.headers.update({"DELL-EMC-TOKEN": str(self.token)})
            return True
        return False

    def __init__(self, ip, username, password):
        self.base_url = f"https://{ip}/api/rest"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = False
        self.token = None
        self.appliance_id = []
        self.cluster_id = []
        self.host_id = []
        self.host_group_id = []
        self.node_id = []
        self.volume_id = []
        self.volume_group_id = []
        self.isAuthenticated = False
        self.points:list[Point] = []  # Liste pour stocker les points à envoyer à InfluxDB
        if self.authenticate():
            self.isAuthenticated = True

    def get_ids(self, entity):
        url = f"{self.base_url}/{entity}"
        response = self.session.get(url)
        if response.status_code == 200:
            setattr(self, f"{entity}_id", [item["id"] for item in response.json()])
            return True
        return False

    def get_appliance_id(self):
        response = self.session.get(f"{self.base_url}/appliance")
        if response.status_code == 200:
            self.appliance_id = [appliance["id"] for appliance in response.json()]
            return True
        return False

    def get_cluster_id(self):
        response = self.session.get(f"{self.base_url}/cluster")
        if response.status_code == 200:
            self.cluster_id = [cluster["id"] for cluster in response.json()]
            return True
        return False

    def get_host_id(self):
        response = self.session.get(f"{self.base_url}/host")
        if response.status_code == 200:
            self.host_id = [host["id"] for host in response.json()]
            return True
        return False

    def get_host_group_id(self):
        response = self.session.get(f"{self.base_url}/host_group")
        if response.status_code == 200:
            self.host_group_id = [host_group["id"] for host_group in response.json()]
            return True
        return False

    def get_node_id(self):
        response = self.session.get(f"{self.base_url}/node")
        if response.status_code == 200:
            self.node_id = [node["id"] for node in response.json()]
            return True
        return False

    def get_volume_id(self):
        response = self.session.get(f"{self.base_url}/volume")
        if response.status_code == 200:
            self.volume_id = [volume["id"] for volume in response.json()]
            return True
        return False

    def get_volume_group_id(self):
        response = self.session.get(f"{self.base_url}/volume_group")
        if response.status_code == 200:
            self.volume_group_id = [volume_group["id"] for volume_group in response.json()]
            return True
        return False

    def get_metrics(self, entity, entity_id, interval="One_Hour"):
        url = f"{self.base_url}/metrics/generate"
        payload = {
            "entity": entity,
            "entity_id": entity_id,
            "interval": interval
        }
        response = self.session.post(url, json=payload)
        return response.json() if response.status_code == 200 else None

    def __influx_point(self, id, response, type_id: str):
        for item in response:
            point = (Point("powerstore_performance").time(item["timestamp"]).tag(type_id, id)
                     .tag("response_definition", item["response_definition"])
                     .tag("entity", item["entity"])
                     .tag("datacenter", DC_NAME))
            for k, v in item.items():
                if k not in ["timestamp", type_id, "response_definition", "entity"] and isinstance(v, (int, float)):
                    point.field(k, v)
            self.points.append(point)

    def space_metrics_cluster(self, entity_id):
        return self.get_metrics("space_metrics_by_cluster", entity_id)

    def space_metrics_cluster_p(self):
        if self.get_cluster_id():
            for id in self.cluster_id:
                response = self.get_metrics("space_metrics_by_cluster", id)
                if response:
                    self.__influx_point(id, response, "cluster_id")

    def performance_metrics_node(self, entity_id):
        return self.get_metrics("performance_metrics_by_node", entity_id)

    def performance_metrics_node_p(self):
        if self.get_node_id():
            for id in self.node_id:
                response = self.get_metrics("performance_metrics_by_node", id)
                if response:
                    self.__influx_point(id, response, "node_id")

    def performance_metrics_appliance(self, entity_id):
        return self.get_metrics("performance_metrics_by_appliance", entity_id)

    def performance_metrics_appliance_p(self):
        if self.get_appliance_id():
            for id in self.appliance_id:
                response = self.get_metrics("performance_metrics_by_appliance", id)
                if response:
                    self.__influx_point(id, response, "appliance_id")

    def get_all_metrics(self):
        self.space_metrics_cluster_p()
        self.performance_metrics_node_p()
        self.performance_metrics_appliance_p()


if __name__ == "__main__":
    print(f"--- Start collecting from DELL Powerstore ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

    ps = PowerStoreCollector(POWERSTORE_HOST, POWERSTORE_USER, POWERSTORE_PASSWD)

    if not ps.isAuthenticated:
        print("Unable to Authenticate")
        exit()

    ps.get_all_metrics()

    print("Writing to InfluxDB...")
    for point in ps.points:
        db.write_point(point)

    db.close()
    print("--- End ---")
