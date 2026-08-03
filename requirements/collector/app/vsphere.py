import os
import ssl
from datetime import datetime
from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim
from influxdb_client_3 import Point
from influx_writer import writer as db

VCENTER_HOST = os.environ.get("VCENTER_HOST", "localhost")
VCENTER_USER = os.environ.get("VCENTER_USER", "")
VCENTER_PASSWORD = os.environ.get("VCENTER_PASSWORD", "")
DS_FOLDER = os.getenv("DS_FOLDER")

class VsphereCollector:
    def __init__(self, host: str, user: str, password: str):
        self.ssl_context = ssl._create_unverified_context()
        self.session = None
        try:
            self.session = SmartConnect(host=host, user=user, pwd=password, sslContext=self.ssl_context)
        except Exception as e:
            raise ConnectionError(f"Unable to connect to vSphere ({host}): {e}")
        if not self.session:
            raise ConnectionError("SmartConnect return None.")
        self.content = self.session.RetrieveContent()
        self.points: list[Point] = []

    def __del__(self):
        if getattr(self, "session", None):
            Disconnect(self.session)

    def find_datastore_folder(self, folder_name: str):
        container = self.content.viewManager.CreateContainerView(
            container=self.content.rootFolder,
            type=[vim.Folder],
            recursive=True,
        )
        found_folder = None
        for folder in container.view:
            if folder.name == folder_name:
                found_folder = folder
                break

        container.Destroy()
        return found_folder

    def get_ds_data(self, folder_name: str):
        ds_folder = self.find_datastore_folder(folder_name)

        if not ds_folder:
            print(f"❌ Folder '{folder_name}' not found.")
            return False

        container = self.content.viewManager.CreateContainerView(
            container=ds_folder,
            type=[vim.Datastore],
            recursive=True,
        )

        for ds in container.view:
            if ds.summary and ds.summary.accessible:
                capacity_gb = ds.summary.capacity / (1024 ** 3)
                free_space_gb = ds.summary.freeSpace / (1024 ** 3)
                space_use_gb = capacity_gb - free_space_gb
                percent_use = (
                    (space_use_gb / capacity_gb) * 100 if capacity_gb > 0 else 0
                )

                point = Point("datastore_usage").tag("datastore_data", ds.name).tag("type", ds.summary.type)
                point.tag("datastore_folder", folder_name).field("total_capacity", round(capacity_gb, 2))
                point.field("free_space", round(free_space_gb, 2)).field("space_use", round(space_use_gb, 2))
                point.field("percent_use", round(percent_use, 2))

                self.points.append(point)

        container.Destroy()
        return True

if __name__ == "__main__":
    print(f"--- Start collecting from VMware vSphere Client ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

    try:
        vsphere = VsphereCollector(host=VCENTER_HOST, user=VCENTER_USER, password=VCENTER_PASSWORD)

        vsphere.get_ds_data(str(DS_FOLDER))
    except Exception as e:
        print(f"❌ Error: {e}")
        exit()

    print("Writing to InfluxDB...")
    for point in vsphere.points:
        db.write_point(point)

    db.close()
    print("--- End ---")