import os
from datetime import datetime

import requests
import urllib3
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Désactiver les avertissements SSL pour les certificats auto-signés (vCenter de test/prod interne)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# CONFIGURATION
# ==========================================
VCENTER_HOST = "vcenter.tondomaine.local"
VCENTER_USER = "api-mon-user@vsphere.local"
VCENTER_PASSWORD = (
    "TonMotDePasseSecret"  # À sécuriser via var d'environnement idéalement
)

INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "TonTokenInfluxDB"
INFLUXDB_ORG = "MonOrganisation"
INFLUXDB_BUCKET = "vmware_metrics"


# ==========================================
# FONCTIONS DE COLLECTE vCENTER (API REST)
# ==========================================
def get_vcenter_session():
    """Authentification auprès du vCenter et récupération du token de session."""
    url = f"https://{VCENTER_HOST}/api/session"
    try:
        response = requests.post(
            url, auth=(VCENTER_USER, VCENTER_PASSWORD), verify=False, timeout=10
        )
        response.raise_for_status()
        # Le token de session est renvoyé directement dans le corps de la réponse en JSON string
        session_token = response.json()
        return session_token
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion au vCenter : {e}")
        return None


def collect_vm_data(session_token):
    """Récupération de la liste des VMs et de leurs caractéristiques de base."""
    url = f"https://{VCENTER_HOST}/api/vcenter/vm"
    headers = {"vmware-api-session-id": session_token}

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        return response.json()  # Retourne la liste des VMs
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des VMs : {e}")
        return []


# ==========================================
# ENVOI DES DONNÉES VERS INFLUXDB
# ==========================================
def send_to_influxdb(vms_list):
    """Formate et envoie les données des VMs vers InfluxDB."""
    if not vms_list:
        print("⚠ Aucune donnée à envoyer à InfluxDB.")
        return

    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)

        points = []
        for vm in vms_list:
            # Filtrage et formatage des données
            # L'API vCenter retourne généralement : vm, name, power_state, cpu_count, memory_size_MiB
            vm_name = vm.get("name")
            power_state = vm.get("power_state")
            cpu_count = vm.get("cpu_count")
            memory_mb = vm.get("memory_size_MiB")

            # Création d'un point de mesure pour InfluxDB
            point = (
                Point("virtual_machines")
                .tag("vm_name", vm_name)
                .tag("vm_id", vm.get("vm"))
                .field("cpu_count", int(cpu_count))
                .field("memory_mb", int(memory_mb))
                .field("is_powered_on", 1 if power_state == "POWERED_ON" else 0)
                .time(datetime.utcnow(), WritePrecision.NS)
            )

            points.append(point)

        # Écriture en bloc (Batch) pour de meilleures performances
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
        print(f"✅ {len(points)} métriques de VMs envoyées avec succès à InfluxDB.")

        client.close()
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture dans InfluxDB : {e}")


# ==========================================
# SCRIPT PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print(
        f"--- Démarrage de la collecte VMware ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---"
    )

    # 1. Connexion au vCenter
    token = get_vcenter_session()

    if token:
        print("🔒 Authentification vCenter réussie.")

        # 2. Collecte
        print("📊 Collecte des données des VMs en cours...")
        vms = collect_vm_data(token)

        # 3. Stockage
        if vms:
            print(f"Total de VMs trouvées : {len(vms)}")
            send_to_influxdb(vms)

        print("--- Fin de la collecte ---")
    else:
        print("🛑 Impossible de continuer sans session vCenter valide.")
