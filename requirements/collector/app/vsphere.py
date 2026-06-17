import os
from datetime import datetime

import requests
import urllib3
from influx_writer import writer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VCENTER_HOST = os.environ.get("VCENTER_HOST")
VCENTER_USER = os.environ.get("VCENTER_USER")
VCENTER_PASSWORD = os.environ.get("VCENTER_PASSWORD")


def get_vcenter_session():
    url = f"https://{VCENTER_HOST}/api/session"
    if not VCENTER_USER or not VCENTER_PASSWORD:
        print("❌ VCENTER_USER or VCENTER_PASSWORD not define")
        return None
    try:
        response = requests.post(
            url, auth=(VCENTER_USER, VCENTER_PASSWORD), verify=False, timeout=10
        )
        response.raise_for_status()
        session_token = response.json()
        return session_token
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting vCenter : {e}")
        return None


def collect_vm_data(session_token):
    url = f"https://{VCENTER_HOST}/api/vcenter/vm"
    headers = {"vmware-api-session-id": session_token}

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving VM data : {e}")
        return []


if __name__ == "__main__":
    print(
        f"--- Start collecting from VMware Vsphere ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---"
    )

    token = get_vcenter_session()

    if token:
        print("🔒 vCenter authentification successful.")

        print("📊 Collecting data from the VMs...")
        vms = collect_vm_data(token)

        if vms:
            print(f"Number of VMs found: {len(vms)}")
            writer.write_records(vms)
            writer.close()

        print("--- End ---")
    else:
        print("🛑 vCenter session not valid. Aborting...")
