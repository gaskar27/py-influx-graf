# Documentation — py-influx-graf

Index de la documentation du projet. Pour démarrer rapidement, voir le [README](../README.md).

## Guides

| Document | Contenu |
|---|---|
| [README](../README.md) | Installation, configuration, démarrage rapide et commandes Make |
| [Documentation technique](DOCUMENTATION_TECHNIQUE.md) | Architecture, services Docker, collecteurs, modèle de données, sécurité |
| [Guide utilisateur Grafana](GRAFANA.md) | Dashboards, export CSV, troubleshooting et cas d'usage |

## Collecteurs (détails par module)

Tous les collecteurs écrivent dans InfluxDB via le singleton `writer` de [`influx_writer.py`](collector/influx_writer.md) et lisent leurs credentials via [`get_secrets()`](collector/utils.md).

| Module | Fichier source | Mesures InfluxDB |
|---|---|---|
| [aria.py](collector/aria.md) | `requirements/collector/app/aria.py` | `cluster_metrics`, `vm_lifecycle` |
| [vsphere.py](collector/vsphere.md) | `requirements/collector/app/vsphere.py` | `datastore_usage` |
| [powerstore.py](collector/powerstore.md) | `requirements/collector/app/powerstore.py` | `powerstore_performance` |
| [unity.py](collector/unity.md) | `requirements/collector/app/unity.py` | `unity_metrics` |

### Modules partagés

| Module | Fichier source | Rôle |
|---|---|---|
| [influx_writer.py](collector/influx_writer.md) | `requirements/collector/app/influx_writer.py` | Abstraction d'écriture InfluxDB (singleton `writer`) |
| [utils.py](collector/utils.md) | `requirements/collector/app/utils.py` | Lecture des secrets Docker (`get_secrets`) |
| [main.py](collector/main.md) | `requirements/collector/app/main.py` | Orchestrateur PowerStore + Unity + vSphere (collector1/2) |

## Parcours de lecture conseillé

1. [README](../README.md) — mettre en route le stack.
2. [Documentation technique](DOCUMENTATION_TECHNIQUE.md) — comprendre l'architecture et le modèle de données.
3. [Collecteurs](collector/aria.md) — détail de chaque module de collecte.
4. [Grafana](GRAFANA.md) — exploiter les dashboards et exporter les données.