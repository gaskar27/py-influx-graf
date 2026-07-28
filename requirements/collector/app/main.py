# import urllib3
import subprocess


# Désactiver les avertissements SSL pour les certificats auto-signés
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

scripts = ["powerstore.py", "unity.py", "vsphere.py"]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python3", script])

print("All scripts have been executed.")
