# powerstore.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Collecteur de metriques Dell PowerStore.

## Position

`requirements/collector/app/powerstore.py`

## Vue d'ensemble

Ce module se connecte a l'API REST d'un Dell PowerStore et collecte les metriques d'espace (clusters) et de performance (noeuds, appliances). Les donnees sont ecrites dans la mesure InfluxDB **`powerstore_performance`**.

## Variables d'environnement

| Variable | Description |
|---|---|
| `DC_NAME` | Nom du datacenter (tag `datacenter`). |
| `NAME` | Nom du fichier secret a lire. |

## Secrets requis (via Docker secrets)

| Cle | Description |
|---|---|
| `POWERSTORE_HOST` | Adresse IP ou FQDN de l'array PowerStore. |
| `POWERSTORE_USER` | Nom d'utilisateur. |
| `POWERSTORE_PASSWD` | Mot de passe. |

## Classe `PowerStoreCollector`

### `__init__(self, ip, username, password)`

- Configure la session HTTP avec authentification Basic (`requests.Session().auth`).
- `verify=False` pour les certificats auto-signes.
- Definit `base_url = https://{ip}/api/rest`.
- Initialise les listes d'IDs : `appliance_id`, `cluster_id`, `host_id`, `host_group_id`, `node_id`, `volume_id`, `volume_group_id`.
- Appelle `authenticate()` immediatement.

### `authenticate(self)`

- Appelle `GET /api/rest/login_session`.
- Extrait le token `DELL-EMC-TOKEN` depuis les headers de reponse.
- Met a jour les headers de session avec ce token.
- Retourne `True`/`False`.

### `get_ids(self, entity)`

- Recupere la liste des IDs pour une entite donnee (appliance, cluster, host, etc.).
- Utilise `setattr()` pour stocker les IDs dynamiquement dans l'instance.
- Retourne `True`/`False`.

### Methodes de recuperation d'IDs

| Methode | Entite | Endpoint |
|---|---|---|
| `get_appliance_id()` | `appliance` | `/api/rest/appliance` |
| `get_cluster_id()` | `cluster` | `/api/rest/cluster` |
| `get_host_id()` | `host` | `/api/rest/host` |
| `get_host_group_id()` | `host_group` | `/api/rest/host_group` |
| `get_node_id()` | `node` | `/api/rest/node` |
| `get_volume_id()` | `volume` | `/api/rest/volume` |
| `get_volume_group_id()` | `volume_group` | `/api/rest/volume_group` |

### `get_metrics(self, entity, entity_id, interval="One_Hour")`

- Appelle `POST /api/rest/metrics/generate`.
- Payload : `entity`, `entity_id`, `interval`.
- Retourne le JSON de la reponse ou `None`.

### `__influx_point(self, id, response, type_id: str)`

- Convertit la reponse API en objets `Point("powerstore_performance")`.
- Tags : identifiant de l'entite (selon `type_id` : `cluster_id`, `node_id`, ou `appliance_id`), `response_definition`, `entity`, `datacenter`.
- Fields : toutes les cles numeriques (int/float) de la reponse.
- Utilise le timestamp de la reponse via `.time(item["timestamp"])`.

### Methodes de collecte

| Methode | Entity | Description |
|---|---|---|
| `space_metrics_cluster(entity_id)` | `space_metrics_by_cluster` | Metriques d'espace d'un cluster. |
| `space_metrics_cluster_p()` | - | Parcourt tous les clusters et collecte les metriques d'espace. |
| `performance_metrics_node(entity_id)` | `performance_metrics_by_node` | Metriques de performance d'un noeud. |
| `performance_metrics_node_p()` | - | Parcourt tous les noeuds et collecte les metriques. |
| `performance_metrics_appliance(entity_id)` | `performance_metrics_by_appliance` | Metriques de performance d'une appliance. |
| `performance_metrics_appliance_p()` | - | Parcourt toutes les appliances et collecte les metriques. |

### `get_all_metrics(self)`

- Point d'entree principal.
- Appelle `space_metrics_cluster_p()`, `performance_metrics_node_p()`, `performance_metrics_appliance_p()`.

## Execution

```python
if __name__ == "__main__":
    s = get_secrets(NAME)
    ps = PowerStoreCollector(s["POWERSTORE_HOST"], s["POWERSTORE_USER"], s["POWERSTORE_PASSWD"])
    if not ps.isAuthenticated: exit()
    ps.get_all_metrics()
    for point in ps.points: db.write_point(point)
    db.close()
```

## Format des donnees InfluxDB

### `powerstore_performance`

| Element | Valeur |
|---|---|
| Measurement | `powerstore_performance` |
| Timestamp | Depuis la reponse API (precision ms) |
| Tag `cluster_id` / `node_id` / `appliance_id` | ID de l'entite |
| Tag `response_definition` | Definition de la metrique PowerStore |
| Tag `entity` | Type d'entite (ex: `space_metrics_by_cluster`) |
| Tag `datacenter` | Valeur de `DC_NAME` |
| Fields | Dynamiques selon les metriques PowerStore (float/int) |

## Voir aussi

- [influx_writer.py](influx_writer.md) — singleton `writer` utilisé pour les écritures
- [utils.py](utils.md) — `get_secrets()` pour la lecture des credentials
- [main.py](main.md) — orchestrateur qui exécute PowerStore dans `collector1`/`collector2`
- [unity.py](unity.md) — collecteur du stockage Dell Unity (dashboard « Dell Storage Systems » partagé)
- [Guide Grafana](../GRAFANA.md) — dashboard « Dell Storage Systems »
