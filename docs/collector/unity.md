# unity.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Collecteur de metriques Dell Unity.

## Position

`requirements/collector/app/unity.py`

## Vue d'ensemble

Ce module se connecte a l'API REST d'un Dell Unity et collecte les metriques systeme, de stockage (pools, LUNs, filesystems, disques) et des processeurs de stockage (SP). Les donnees sont ecrites dans la mesure InfluxDB **`unity_metrics`**.

## Variables d'environnement

| Variable | Description |
|---|---|
| `DC_NAME` | Nom du datacenter (tag `datacenter`). |
| `NAME` | Nom du fichier secret a lire. |

## Secrets requis (via Docker secrets)

| Cle | Description |
|---|---|
| `UNITY_HOST` | Adresse IP ou FQDN de l'array Unity. |
| `UNITY_USER` | Nom d'utilisateur. |
| `UNITY_PASSWD` | Mot de passe. |

## Classe `UnityCollector`

### `__init__(self, ip, username, password)`

- Configure la session HTTP avec authentification Basic.
- Headers specifiques : `X-EMC-REST-CLIENT: true`, `Accept: application/json`.
- `verify=False` pour les certificats auto-signes.
- Definit `base_url = https://{ip}/api`.
- Appelle `authenticate()` immediatement.

### `authenticate(self)`

- Appelle `GET /api/types/loginSessionInfo/instances`.
- Extrait le token `EMC-CSRF-TOKEN` depuis les headers.
- Met a jour les headers de session avec ce token (protection CSRF).
- Retourne `True`/`False`.

### `get_metrics(self, type, fields=None, filter=None)`

- Appelle `GET /api/types/{type}/instances`.
- Parametres optionnels : `fields` (champs a recuperer), `filter` (filtre OData).
- Retourne la liste `entries` du JSON de reponse ou `None`.

### `__influx_point(self, response)`

- Convertit les reponses API en objets `Point("unity_metrics")` pour les ressources standard.
- Tags : `name`, `id`, `datacenter`.
- Fields : toutes les cles du `content` sauf `name` et `id`.
- Utilise le timestamp `item["updated"]`.

### `__influx_point_sp(self, response)`

- Methode specifique pour les processeurs de stockage (SP).
- Gere la structure imbriquee du champ `values` : chaque cle/valeur du sous-objet `values` est ajoutee comme field.
- Gere egalement un champ `timestamp` imbrique pour le timestamp du point.

### Methodes de collecte

| Methode | Type Unity | Champs recuperes |
|---|---|---|
| `get_storage_processor_metrics()` | `metricValue` | Metriques CPU des SP (filtre : `sp.*.cpu.summary.utilization`) |
| `get_system_metrics()` | `system` | `name`, `model`, `serialNumber` |
| `get_pool_metrics()` | `pool` | `name`, `sizeTotal`, `sizeUsed`, `sizeSubscribed` |
| `get_luns_metrics()` | `luns` | `name`, `sizeAllocated`, `sizeTotal`, `pool` |
| `get_filesystem_metrics()` | `filesystem` | `name`, `sizeAllocated`, `sizeTotal` |
| `get_disk_metrics()` | `disk` | `name`, `sizeAllocated`, `sizeTotal` |

### `get_all_metrics(self)`

- Point d'entree principal.
- Appelle toutes les methodes de collecte dans l'ordre : SP, system, pools, LUNs, filesystems, disques.

## Execution

```python
if __name__ == "__main__":
    s = get_secrets(NAME)
    unity = UnityCollector(s["UNITY_HOST"], s["UNITY_USER"], s["UNITY_PASSWD"])
    if not unity.isAuthenticated: exit()
    unity.get_all_metrics()
    for point in unity.points: db.write_point(point)
    db.close()
```

## Format des donnees InfluxDB

### `unity_metrics`

| Element | Valeur |
|---|---|
| Measurement | `unity_metrics` |
| Timestamp | Depuis `updated` ou `timestamp` de la reponse (precision ms) |
| Tag `name` | Nom de la ressource Unity |
| Tag `id` | Identifiant Unity de la ressource |
| Tag `datacenter` | Valeur de `DC_NAME` |
| Fields | Dynamiques selon le type de ressource |

### Details des fields par type de ressource

| Type | Fields |
|---|---|
| **System** | `model`, `serialNumber` |
| **Pool** | `sizeTotal`, `sizeUsed`, `sizeSubscribed` |
| **LUNs** | `sizeAllocated`, `sizeTotal`, `pool` |
| **Filesystem** | `sizeAllocated`, `sizeTotal` |
| **Disk** | `sizeAllocated`, `sizeTotal` |
| **Storage Processor** | Metriques CPU dynamiques (ex: `avg_utilization`, etc.) |

## Voir aussi

- [influx_writer.py](influx_writer.md) — singleton `writer` utilisé pour les écritures
- [utils.py](utils.md) — `get_secrets()` pour la lecture des credentials
- [main.py](main.md) — orchestrateur qui exécute Unity dans `collector1`/`collector2`
- [powerstore.py](powerstore.md) — collecteur du cluster PowerStore (dashboard « Dell Storage Systems » partagé)
- [Guide Grafana](../GRAFANA.md) — dashboard « Dell Storage Systems »
