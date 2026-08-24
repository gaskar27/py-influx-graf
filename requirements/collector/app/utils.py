import os

def get_secrets(secret_file):
    secret_path = f"/run/secrets/{secret_file}"
    secrets = {}
    if os.path.exists(secret_path):
        with open(secret_path, "r") as f:
            for line in f:

                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key] = value
            return secrets if secrets else None
    return None
