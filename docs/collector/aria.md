# aria.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Collecteur de metriques VMware Aria Operations.

## Position

`requirements/collector/app/aria.py`

## Vue d'ensemble

Ce module collecte les metriques de clusters et le cycle de vie des VMs depuis l'API Aria Operations (anciennement vRealize Operations). Les donnees sont ecrites dans deux mesures InfluxDB :

- **`cluster_metrics`** : metriques CPU, memoire, nombre de VMs et operations VM par cluster.
- **`vm_lifecycle`** : etat de creation/destruction des VMs.

## Variables d'environnement

| Variable | Description |
|---|---|
| `ARIA_RESOURCE_ID1` | Identifiant de l'instance Aria pour le premier datacenter. |
| `ARIA_RESOURCE_ID2` | Identifiant de l'instance Aria pour le deuxieme datacenter. |
| `MAP_ID1` | Nom d'affichage (tag `datacenter`) pour le premier datacenter. |
| `MAP_ID2` | Nom d'affichage (tag `datacenter`) pour le deuxieme datacenter. |

## Secrets requis (via Docker secrets)

| Cle | Description |
|---|---|
| `ARIA_HOST` | Hostname de l'instance Aria Operations. |
| `ARIA_USER` | Nom d'utilisateur pour l'authentification. |
| `ARIA_PASSWD` | Mot de passe. |
| `ARIA_AUTH_SOURCE` | Source d'authentification (realm). |

## Classe `AriaCollector`

### `__init__(self, host: str, authentification: dict)`

- Configure la session HTTP avec `verify=False` (certificats auto-signes).
- Obtient un token d'authentification via `__get_token()`.
- Definit une fenetre temporelle de **30 jours** (`begin` / `end` en millisecondes).
- Initialise `names_map` : correspondance `ARIA_RESOURCE_ID -> MAP_ID` (datacenter name).
- Initialise deux listes : `lines` (line protocol) et `points` (objets Point).

### `__get_token(self, payload: dict)`

- Appelle `POST /suite-api/api/auth/token/acquire`.
- Retourne le token d'acces.
- En cas d'echec : `SystemExit` avec le detail de l'erreur.

### `__influx_line_protocol(self, data_json, measurement, datacenter_id, cluster_name, cluster_id)`

- Convertit la reponse JSON de l'API Aria en lignes InfluxDB line protocol.
- Groupe les metriques par timestamp.
- Gere les types : entiers suffixes par `i`, flottants bruts.
- Echappe les espaces dans les noms de datacenter (`\ `).
- Tagguage : `datacenter`, `name` (cluster), `id` (cluster).

### `__get_vm_destroy_date(self, identifier: str)`

- Appelle `GET /suite-api/api/resources/{identifier}/stats/latest`.
- Extrait le premier timestamp de la reponse (date de destruction).
- Retourne `None` si pas de donnees.

### `__convert_to_influx_point(self, data, instance_id)`

- Convertit la liste des VMs en objets `Point` pour la mesure `vm_lifecycle`.
- Chaque VM a :
  - Tag `datacenter` : nom du datacenter (via `names_map`).
  - Tag `name` : nom de la VM.
  - Tag `id` : identifiant Aria de la VM.
  - Field `is_deleted` : booleen, `True` si `resourceState == "NOT_EXISTING"`.
  - Field `created_at` : timestamp de creation (int, nullable).
  - Field `destroyed_at` : timestamp de destruction (int, nullable, appele via `__get_vm_destroy_date`).

### `cluster_workload(self, datacenter_id, cluster_name, cluster_id)`

- Requete : `POST /suite-api/api/resources/stats/query`.
- Stat keys : `cpu|capacity_usagepct_average`, `mem|host_usagePct`.
- Rollup : `MAX`, intervalle : 1 jour.
- Ecrit dans `cluster_metrics`.

### `cluster_vms(self, datacenter_id, cluster_name, cluster_id)`

- Meme endpoint que `cluster_workload`.
- Stat keys : `summary|total_number_vms`, `summary|number_running_vms`.
- Rollup : `LATEST`.
- Ecrit dans `cluster_metrics`.

### `cluster_vmop(self, datacenter_id, cluster_name, cluster_id)`

- Meme endpoint.
- Stat keys : `vmop|inventoryChange|numCreate_latest`, `vmop|inventoryChange|numDestroy_latest`.
- Rollup : `SUM`.
- Ecrit dans `cluster_metrics`.

### `get_cluster_metric(self, resource_id: str)`

- Recupere la liste des clusters via `GET /suite-api/api/resources?adapterInstanceId=...&adapterKind=VMWARE&resourceKind=ClusterComputeResource`.
- Pour chaque cluster, appelle `cluster_workload`, `cluster_vms`, `cluster_vmop`.

### `get_vms_resource_stat(self, adapter_instance_id: str)`

- Requete : `POST /suite-api/api/resources/query` avec `resourceKind=VirtualMachine`.
- Passe le resultat a `__convert_to_influx_point()`.

### `collect(self)`

- Point d'entree principal.
- Appelle `get_cluster_metric` et `get_vms_resource_stat` pour les deux datacenters (`ARIA_RESOURCE_ID1` et `ARIA_RESOURCE_ID2`).

## Execution

```python
if __name__ == "__main__":
    s = get_secrets("aria_s")
    auth = {"username": s["ARIA_USER"], "authSource": s["ARIA_AUTH_SOURCE"], "password": s["ARIA_PASSWD"]}
    aria = AriaCollector(s["ARIA_HOST"], auth)
    aria.collect()
    # Ecriture dans InfluxDB
    for line in aria.lines: db.write_line(line)
    for point in aria.points: db.write_point(point)
    db.close()
```

## Format des donnees InfluxDB

### `cluster_metrics`

```
cluster_metrics,datacenter=<dc>,name=<cluster>,id=<id> <field>=<value>... <timestamp_ns>
```

Fields dynamiques selon les stat keys recuperees.

### `vm_lifecycle`

Objet Point avec :
- Tags : `datacenter`, `name`, `id`
- Fields : `is_deleted` (bool), `created_at` (int), `destroyed_at` (int)

## Voir aussi

- [influx_writer.py](influx_writer.md) — singleton `writer` utilisé pour les écritures
- [utils.py](utils.md) — `get_secrets()` pour la lecture des credentials
- [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) — modèle de données `cluster_metrics` / `vm_lifecycle`
- [Guide Grafana](../GRAFANA.md) — dashboard « VMware Aria Operations »
