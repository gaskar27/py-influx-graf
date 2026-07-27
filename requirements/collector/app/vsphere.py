import os
from pyVim.connect import Disconnect, SmartConnectNoSSL
from pyVmomi import vim

VCENTER_HOST = os.environ.get("VCENTER_HOST")
VCENTER_USER = os.environ.get("VCENTER_USER")
VCENTER_PASSWORD = os.environ.get("VCENTER_PASSWORD")

class VsphereCollector:
    def __init__(self, host, user, password):
        self.session = SmartConnectNoSSL(host=host, user=user, pwd=password)
        self.points = []

    def __del__(self):
        Disconnect(self.session)
