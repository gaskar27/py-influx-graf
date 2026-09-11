# vsphere.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Collecteur de metriques d'utilisation des datastores VMware vSphere.

## Position

`requirements/collector/app/vsphere.py`

## Vue d'ensemble

Ce module se connecte a un serveur vCenter via pyvmomi (`SmartConnect`) et collecte les metriques d'espace de stockage des datastores situes dans un folder specifique. Les donnees sont ecrites dans la mesure InfluxDB **`datastore_usage`**.

## Variables d'environnement

| Variable | Description |
|---|---|
| `DS_FOLDER` | Nom du folder vSphere contenant les datastores a surveiller. |
| `DC_NAME` | Nom du datacenter VMware (utilise comme tag `datacenter`). |
| `NAME` | Nom du fichier secret a lire (ex: `one_s` ou `two_s`). |

## Secrets requis (via Docker secrets)

| Cle | Description |
|---|---|
| `VCENTER_HOST` | Adresse IP ou FQDN du serveur vCenter. |
| `VCENTER_USER` | Nom d'utilisateur vCenter. |
| `VCENTER_PASSWD` | Mot de passe vCenter. |

## Classe `VsphereCollector`

### `__init__(self, host: str, user: str, password: str)`

- Cree un contexte SSL non verifie (`ssl._create_unverified_context()`) pour gerer les certificats auto-signes.
- Se connecte via `SmartConnect(host, user, pwd, sslContext)`.
- Recupere le contenu racine via `session.RetrieveContent()`.
- Initialise la liste `points` pour stocker les objets `Point`.
- En cas d'echec de connexion, lève `ConnectionError`.

### `__del__(self)`

- Appele `Disconnect(session)` pour fermer proprement la connexion vSphere.

### `find_datastore_folder(self, folder_name: str)`

- Cree un `ContainerView` recursif sur le `rootFolder` pour les objets `vim.Folder`.
- Parcourt les vues pour trouver un folder au nom correspondant.
- Detruit le container view apres usage.
- Retourne le folder trouve ou `None`.

### `get_ds_data(self, folder_name: str)`

- Appelle `find_datastore_folder()` pour localiser le folder.
- Si le folder n'existe pas, affiche une erreur et retourne `False`.
- Cree un `ContainerView` sur le folder pour les objets `vim.Datastore`.
- Pour chaque datastore accessible (`ds.summary.accessible`) :
  - Calcule `capacity_gb`, `free_space_gb`, `space_use_gb`, `percent_use`.
  - Cree un objet `Point("datastore_usage")` avec :
    - Tags : `datastore_data` (nom), `type` (VMFS, NFS...), `datastore_folder`, `datacenter`.
    - Fields : `total_capacity`, `free_space`, `space_use`, `percent_use` (tous arrondis a 2 decimales).
- Detruit le container view.
- Retourne `True` en cas de succes.

## Execution

```python
if __name__ == "__main__":
    s = get_secrets(NAME)
    vsphere = VsphereCollector(
        host=s["VCENTER_HOST"],
        user=s["VCENTER_USER"],
        password=s["VCENTER_PASSWD"]
    )
    vsphere.get_ds_data(str(DS_FOLDER))
    for point in vsphere.points: db.write_point(point)
    db.close()
```

## Format des donnees InfluxDB

### `datastore_usage`

| Element | Valeur |
|---|---|
| Measurement | `datastore_usage` |
| Tag `datastore_data` | Nom du datastore |
| Tag `type` | Type (VMFS, NFS, etc.) |
| Tag `datastore_folder` | Folder vSphere parent |
| Tag `datacenter` | Valeur de `DC_NAME` |
| Field `total_capacity` | Capacite totale en GB (float, 2 dec.) |
| Field `free_space` | Espace libre en GB (float, 2 dec.) |
| Field `space_use` | Espace utilise en GB (float, 2 dec.) |
| Field `percent_use` | Pourcentage d'utilisation (float, 2 dec.) |

## Voir aussi

- [influx_writer.py](influx_writer.md) — singleton `writer` utilisé pour les écritures
- [utils.py](utils.md) — `get_secrets()` pour la lecture des credentials
- [main.py](main.md) — orchestrateur qui exécute vSphere dans `collector1`/`collector2`
- [Guide Grafana](../GRAFANA.md) — dashboards « Infrastructure Overview » et « VMware vSphere - Datastores »
