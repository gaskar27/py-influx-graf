import subprocess

scripts = ["powerstore.py", "unity.py", "vsphere.py"]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python3", script])

print("All scripts have been executed.")
