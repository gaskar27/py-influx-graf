# influx_writer.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Module d'abstraction pour l'ecriture de metriques dans InfluxDB.

## Position

`requirements/collector/app/influx_writer.py`

## Vue d'ensemble

Ce module fournit la classe `InfluxDBWriter` qui encapsule toute la logique de connexion et d'ecriture vers InfluxDB. Un singleton `writer` est instancie au niveau du module et importe par tous les collecteurs (`aria.py`, `vsphere.py`, `powerstore.py`, `unity.py`) via :

```python
from influx_writer import writer as db
```

> **Important :** Aucun collecteur ne doit instancier `InfluxDBClient` directement. Toutes les ecritures passent par ce module.

## Variables d'environnement

| Variable | Defaut | Description |
|---|---|---|
| `INFLUXDB_TOKEN` | `""` | Token d'authentification InfluxDB. Si absent, un warning est logge. |
| `INFLUXDB_BUCKET` | `"local_system"` | Nom de la base de donnees InfluxDB. |
| `INFLUXDB_HOST` | `"influxdb3"` | Hostname du serveur InfluxDB. |
| `INFLUXDB_PORT` | `"8181"` | Port du serveur InfluxDB. |

## Classe `InfluxDBWriter`

### `__init__(self)`

- Lit les variables d'environnement pour la configuration.
- Appelle `_create_database_if_not_exists()` pour creer la base avec une retention de **90 jours** si elle n'existe pas.
- Configure les `WriteOptions` du client batch :
  - `batch_size=500`
  - `flush_interval=10_000 ms`
  - `jitter_interval=2_000 ms`
  - `retry_interval=5_000 ms`
  - `max_retries=5`
  - `max_retry_delay=30_000 ms`
  - `exponential_base=2`
- Instancie `InfluxDBClient3` avec les callbacks de succes/erreur/retry.

### `_create_database_if_not_exists(self)`

- Appelle l'API REST `POST /api/v3/configure/database` pour creer la base.
- Retention period : `90d`.
- Gere les codes HTTP : `200/201` (creation), `409` (deja existante), autres (debug).
- En cas d'echec de l'appel HTTP, logge un warning (pas d'exception fatale).

### `write_point(self, point: Point)`

- Ecrit un seul objet `Point` dans InfluxDB.
- Precision d'ecriture : `ms`.
- En cas d'echec, logge une erreur.

### `write_records(self, records: Union[List[Point], List[Dict], Point, Dict])`

- Ecrit un ou plusieurs enregistrements (objets `Point` ou dictionnaires).
- Precision d'ecriture : `ms`.

### `write_line(self, line: str)`

- Ecrit une chaine au format InfluxDB line protocol.
- Utilise par `aria.py` pour les metriques de cluster (format line protocol brut).

### `close(self)`

- Ferme la connexion client InfluxDB.

## Singleton

```python
writer = InfluxDBWriter()
```

Instancie au chargement du module. Tous les collecteurs partagent cette meme instance.

## Callbacks de batch

Trois fonctions definies au niveau du module :

| Fonction | Role |
|---|---|
| `success(self, data)` | Appelee en cas de succes d'ecriture d'un batch. |
| `error(self, data, err)` | Appelee en cas d'erreur. |
| `retry(self, data, err)` | Appelee en cas de tentative de retry. |

## Collecteurs utilisant ce module

Tous les collecteurs importent le singleton `writer` :

```python
from influx_writer import writer as db
```

- [aria.py](aria.md) — écrit `cluster_metrics` (via `write_line`) et `vm_lifecycle` (via `write_point`)
- [vsphere.py](vsphere.md) — écrit `datastore_usage` (via `write_point`)
- [powerstore.py](powerstore.md) — écrit `powerstore_performance` (via `write_point`)
- [unity.py](unity.md) — écrit `unity_metrics` (via `write_point`)
