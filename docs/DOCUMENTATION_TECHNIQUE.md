# Documentation Technique - py-influx-graf

> **Navigation :** [README](../README.md) · [Index de la documentation](README.md) · [Guide utilisateur Grafana](GRAFANA.md) · [Détails des collecteurs](collector/)

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Prérequis](#3-prérequis)
4. [Installation et configuration](#4-installation-et-configuration)
5. [Structure du projet](#5-structure-du-projet)
6. [Services Docker](#6-services-docker)
7. [Système de collecte de données](#7-système-de-collecte-de-données)
8. [Modèle de données InfluxDB](#8-modèle-de-données-influxdb)
9. [Grafana et visualisation](#9-grafana-et-visualisation)
10. [Gestion des secrets](#10-gestion-des-secrets)
11. [Variables d'environnement](#11-variables-denvironnement)
12. [Commandes Makefile](#12-commandes-makefile)
13. [Dockerfile et entrypoint](#13-dockerfile-et-entrypoint)
14. [Problèmes connus](#14-problèmes-connus)
15. [Sécurité](#15-sécurité)

---

## 1. Vue d'ensemble

**py-influx-graf** est une application Docker multi-conteneurs qui collecte des métriques d'infrastructure virtualisée et de stockage, les stocke dans InfluxDB 3, et les visualise via Grafana.

### Sources de données collectées

| Source | Technologie | Type de données |
|--------|------------|-----------------|
| VMware Aria Operations | API REST (suite-api) | Métriques de clusters, cycle de vie des VMs |
| VMware vSphere | pyvmomi (SDK) | Utilisation des datastores |
| Dell PowerStore | API REST | Métriques de performance et d'espace |
| Dell Unity | API REST | Métriques de stockage, LUNs, filesystems, SP |

### Stack technologique

- **Conteneurisation** : Docker Compose
- **Base de donnée** : InfluxDB 3.9.3-core (port 8181)
- **Visualisation** : Grafana (port 3000)
- **Langage** : Python 3 (conteneur Alpine)
- **Collecteurs** : Scripts Python individuels pour chaque source

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Docker Compose                          │
│                                                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ influxdb3   │  │   grafana    │  │   Collecteurs        │   │
│  │ :8181       │  │   :3000      │  │                      │   │
│  │             │  │              │  │  ┌────────────────┐  │   │
│  │  Base 90j   │◄─┤  Datasource  │  │  │ aria_collector │  │   │
│  │  retention  │  │  InfluxDB-v3 │  │  │   (aria.py)    │  │   │
│  │             │  │              │  │  └────────────────┘  │   │
│  │             │  │              │  │  ┌────────────────┐  │   │
│  │             │◄─┤  Dashboards  │  │  │  collector1    │  │   │
│  │             │  │  provisionnés│  │  │  (powerstore,  │  │   │
│  │             │  │              │  │  │   unity,       │  │   │
│  │             │  │              │  │  │   vsphere)     │  │   │
│  │             │  │              │  │  └────────────────┘  │   │
│  │             │  │              │  │  ┌────────────────┐  │   │
│  │             │◄─┤              │  │  │  collector2    │  │   │
│  │             │  │              │  │  │  (powerstore,  │  │   │
│  │             │  │              │  │  │   unity,       │  │   │
│  │             │  │              │  │  │   vsphere)     │  │   │
│  │             │  │              │  │  └────────────────┘  │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                │
│  Volumes : influxdb_data, grafana_data                         │
│  Secrets : aria_s, one_s, two_s                                │
└────────────────────────────────────────────────────────────────┘
```

### Flux de données

```
Infrastructure (vCenter, Aria, PowerStore, Unity)
        │
        ▼
   Collecteurs Python ──► influx_writer.py (singleton)
        │
        ▼
   InfluxDB 3 (90 jours de rétention)
        │
        ▼
   Grafana (dashboards provisionnés)
```

### Instances de collecte

Le système utilise **3 instances de collecteur** permettant la collecte parallèle depuis différentes sources d'infrastructure :

| Instance | Conteneur | Collectes |
|----------|-----------|-----------|
| Aria | `aria_collector` | `aria.py` (Aria Operations) |
| Collector 1 | `collector1` | `powerstore.py`, `unity.py`, `vsphere.py` |
| Collector 2 | `collector2` | `powerstore.py`, `unity.py`, `vsphere.py` |

---

## 3. Prérequis

- Docker et Docker Compose installés
- Accès réseau aux équipements collectés (vCenter, Aria Operations, PowerStore, Unity)
- Fichiers de secrets créés à partir des fichiers `.example`
- Fichier `.env` configuré

---

## 4. Installation et configuration

### 4.1 Cloner le dépôt

```bash
git clone git@github.com:gaskar27/py-influx-graf.git
cd py-influx-graf
```

### 4.2 Configurer l'environnement

```bash
cp .env.example .env
```

Éditer le fichier `.env` avec les valeurs appropriées (voir [Section 11](#11-variables-denvironnement)).

### 4.3 Configurer les secrets

Créer les fichiers de secrets à partir des exemples :

```bash
cp secrets/aria.txt.example secrets/aria.txt
cp secrets/one.txt.example secrets/one.txt
cp secrets/two.txt.example secrets/two.txt
```

Remplir chaque fichier avec les identifiants réels (voir [Section 10](#10-gestion-des-secrets)).

### 4.4 Démarrer le stack

```bash
make start
```

### 4.5 Lancer la collecte

```bash
make collector    # Tous les collecteurs
# ou
make run          # Démarrer + collecter
```

---

## 5. Structure du projet

```
py-influx-graf/
├── compose.yaml                    # Définition des services Docker
├── Makefile                        # Commandes de gestion
├── .env.example                    # Template de variables
├── LICENSE                         # Apache 2.0
├── README.md                       # Documentation utilisateur (FR)
├── AGENTS.md                       # Instructions pour agents OpenCode
├── docs/
│   ├── README.md                   # Index de la documentation
│   ├── DOCUMENTATION_TECHNIQUE.md  # Ce document
│   ├── GRAFANA.md                  # Guide utilisateur Grafana
│   ├── collector/                  # Détails des modules de collecte
│   │   ├── aria.md                 # Collecteur Aria Operations
│   │   ├── vsphere.md              # Collecteur vSphere
│   │   ├── powerstore.md           # Collecteur PowerStore
│   │   ├── unity.md                # Collecteur Unity
│   │   ├── influx_writer.md        # Abstraction d'écriture InfluxDB
│   │   ├── utils.md                # Utilitaires (lecture secrets)
│   │   └── main.md                 # Orchestrateur multi-collecteur
│   └── images/                     # Captures d'écran Grafana
│
├── requirements/
│   ├── collector/
│   │   ├── Dockerfile              # Image Alpine + Python
│   │   ├── .dockerignore           # Fichiers exclus du build
│   │   ├── app/
│   │   │   ├── aria.py             # Collecteur Aria Operations
│   │   │   ├── vsphere.py          # Collecteur vSphere
│   │   │   ├── powerstore.py       # Collecteur PowerStore
│   │   │   ├── unity.py            # Collecteur Unity
│   │   │   ├── main.py             # Orchestrateur multi-collecteur
│   │   │   ├── influx_writer.py    # Abstraction d'écriture InfluxDB
│   │   │   ├── utils.py            # Utilitaires (lecture secrets)
│   │   │   └── requirements.txt    # Dépendances Python
│   │   └── tools/
│   │       ├── entrypoint.sh       # Point d'entrée conteneur
│   │       ├── all.sh              # Exécute tous les collecteurs
│   │       ├── aria.sh             # Exécute aria.py
│   │       ├── powerstore.sh       # Exécute powerstore.py
│   │       ├── unity.sh            # Exécute unity.py
│   │       └── vsphere.sh          # Exécute vsphere.py
│   ├── grafana/
│   └── conf/
│       ├── dashboards/
│       │   ├── dashboards.yml              # Config provider dashboards
│       │   ├── 01-infrastructure-overview.json
│       │   ├── 02-vmware-vsphere.json
│       │   ├── 03-dell-storage.json
│       │   └── 04-aria-operations.json
│       └── datasources/
│           └── datasources.yml             # Config datasource InfluxDB
│
└── secrets/
    ├── aria.txt.example            # Template credentials Aria
    ├── one.txt.example             # Template credentials collector1
    ├── two.txt.example             # Template credentials collector2
    └── not_a_secret.txt            # Placeholder vide
```

---

## 6. Services Docker

### 6.1 influxdb3

| Propriété | Valeur |
|-----------|--------|
| Image | `influxdb:3.9.3-core` |
| Port | 8181 |
| Authentification | Désactivée (`--without-auth`) |
| Stockage | Object-store fichier, répertoire `/var/lib/influxdb3` |
| Volume persistant | `influxdb_data` |
| Rétention | 90 jours (configurée au premier write) |
| Healthcheck | `curl http://localhost:8181/health` |

### 6.2 grafana

| Propriété | Valeur |
|-----------|--------|
| Image | `grafana/grafana:latest` |
| Port | 3000 |
| Identifiants | `${ADMIN}` / `${PASSW}` |
| Provisioning | Monté depuis `./requirements/grafana/conf` |
| Volume persistant | `grafana_data` |

### 6.3 aria_collector

| Propriété | Valeur |
|-----------|--------|
| Build | `./requirements/collector` |
| Commande | `aria` |
| Secret monté | `aria_s` (fichier `./secrets/aria.txt`) |
| Variables | `ARIA_RESOURCE_ID1/2`, `MAP_ID1/2` |
| Dépendance | Attend `influxdb3` sain |

### 6.4 collector1

| Propriété | Valeur |
|-----------|--------|
| Build | `./requirements/collector` |
| Commande | `all` |
| Secret monté | `one_s` (fichier `./secrets/one.txt`) |
| Variables | `DS_FOLDER=${DS_FOLDER1}`, `DC_NAME=${DC_NAME1}` |
| Dépendance | Attend `influxdb3` sain |

### 6.5 collector2

| Propriété | Valeur |
|-----------|--------|
| Build | `./requirements/collector` |
| Commande | `all` |
| Secret monté | `two_s` (fichier `./secrets/two.txt`) |
| Variables | `DS_FOLDER=${DS_FOLDER2}`, `DC_NAME=${DC_NAME2}` |
| Dépendance | Attend `influxdb3` sain |

---

## 7. Système de collecte de données

> Détail complet de chaque module : [collector/](collector/)

### 7.1 influx_writer.py - Abstraction d'écriture

> Documentation détaillée : [collector/influx_writer.md](collector/influx_writer.md)

Le module `influx_writer.py` fournit un singleton `writer` qui encapsule toute interaction avec InfluxDB 3.

**Fonctionnalités :**
- Création automatique de la base de données avec rétention de 90 jours au premier write
- Options d'écriture : batch_size=500, flush_interval=10s, max_retries=5
- Méthodes disponibles :
  - `write_point(point)` : écrit un objet `Point` InfluxDB
  - `write_records(records)` : écrit des lignes de protocole brutes
  - `write_line(line)` : écrit une ligne de protocole unique
- Précision temporelle : millisecondes (`write_precision="ms"`)

**Utilisation :**

```python
from influx_writer import writer
from influxdb3 import Point

# Écriture via Point
point = Point("measurement") \
    .tag("tag_name", "tag_value") \
    .field("field_name", field_value)
writer.write_point(point)

# Écriture via line protocol
writer.write_line("measurement,tag=val field=123")
```

### 7.2 utils.py - Utilitaires

> Documentation détaillée : [collector/utils.md](collector/utils.md)

La fonction `get_secrets(secret_file)` :
- Lit le fichier de secrets depuis `/run/secrets/<secret_file>`
- Parse les paires `clé=valeur`
- Ignore les lignes vides et les commentaires (`#`)
- Retourne un `dict` ou `None` en cas d'erreur

```python
from utils import get_secrets

secrets = get_secrets("one_s")
host = secrets.get("VCENTER_HOST")
```

### 7.3 aria.py - Collecteur Aria Operations

> Documentation détaillée : [collector/aria.md](collector/aria.md)

**Classe :** `AriaCollector`

**Connexion :** API REST avec authentification par token (`OpsToken`) contre `https://{host}/suite-api/api`

**Fenêtre temporelle :** 30 derniers jours (calculée dynamiquement)

**Méthodes de collecte :**

| Méthode | Mesure InfluxDB | Métriques collectées | Rollup |
|---------|-----------------|----------------------|--------|
| `cluster_workload()` | `cluster_metrics` | CPU capacity, Memory usage | MAX (quotidien) |
| `cluster_vms()` | `cluster_metrics` | Total VMs, Running VMs | LATEST (quotidien) |
| `cluster_vmop()` | `cluster_metrics` | VMs créées, VMs détruites | SUM (quotidien) |
| `get_vms_resource_stat()` | `vm_lifecycle` | Statut, dates création/destruction | - |

**Mécanisme d'écriture :**
- `cluster_metrics` : écriture via `write_line()` (line protocol) avec timestamp en millisecondes
- `vm_lifecycle` : écriture via `write_point()` avec objets `Point`

### 7.4 vsphere.py - Collecteur vSphere

> Documentation détaillée : [collector/vsphere.md](collector/vsphere.md)

**Classe :** `VsphereCollector`

**Connexion :** pyvmomi (`SmartConnect`) avec contexte SSL non vérifié (`_create_unverified_context()`)

**Données collectées :**
- Liste des datastores accessibles dans le dossier spécifié (`DS_FOLDER`)
- Pour chaque datastore : `total_capacity`, `free_space`, `space_use`, `percent_use` (en GB, 2 décimales)

**Écriture :** Mesure `datastore_usage` avec tags `datastore_data`, `type`, `datastore_folder`, `datacenter`

### 7.5 powerstore.py - Collecteur PowerStore

> Documentation détaillée : [collector/powerstore.md](collector/powerstore.md)

**Classe :** `PowerStoreCollector`

**Connexion :** API REST avec authentification basique + token de session (`DELL-EMC-TOKEN`)

**Méthodes de collecte :**

| Métrique | Endpoint | Tag principal |
|----------|----------|---------------|
| `space_metrics_by_cluster` | `metrics/generate` | `cluster_id` |
| `performance_metrics_by_node` | `metrics/generate` | `node_id` |
| `performance_metrics_by_appliance` | `metrics/generate` | `appliance_id` |

**Intervalle :** `One_Hour` (dernière heure)

**Écriture :** Mesure `powerstore_performance` avec tags dynamiques (`datacenter`, `response_definition`, `entity`)

### 7.6 unity.py - Collecteur Unity

> Documentation détaillée : [collector/unity.md](collector/unity.md)

**Classe :** `UnityCollector`

**Connexion :** API REST avec authentification basique + jetons `EMC-CSRF-TOKEN` et `X-EMC-REST-CLIENT: true`

**Données collectées :**

| Ressource | Métriques | Filtre |
|-----------|-----------|--------|
| Storage Processor | CPU utilization | `path eq "sp.*.cpu.summary.utilization"` |
| System | model, serialNumber | - |
| Pool | sizeTotal, sizeUsed, sizeSubscribed | - |
| LUN | sizeAllocated, sizeTotal, pool | - |
| Filesystem | sizeAllocated, sizeTotal | - |
| Disk | sizeAllocated, sizeTotal | - |

**Écriture :** Mesure `unity_metrics` avec tags `name`, `id`, `datacenter`

### 7.7 main.py - Orchestrateur

> Documentation détaillée : [collector/main.md](collector/main.md)

Exécute séquentiellement les collecteurs via `subprocess.run(["python3", script])` :
1. `powerstore.py`
2. `unity.py`
3. `vsphere.py`

Utilisé par les conteneurs `collector1` et `collector2`.

---

## 8. Modèle de données InfluxDB

> Adéquation détaillée par collecteur : [collector/](collector/)

### 8.1 cluster_metrics

Collecté par : `aria.py` (Aria Operations)

| Type | Clé | Description |
|------|-----|-------------|
| Tag | `datacenter` | Nom du datacenter/ressource (MAP_ID) |
| Tag | `name` | Nom du cluster |
| Tag | `id` | Identifiant du cluster |
| Field | `cpu_capacity_usagepct_average` | Utilisation CPU (%) - MAX 30j |
| Field | `mem_host_usagePct` | Utilisation mémoire (%) - MAX 30j |
| Field | `summary_total_number_vms` | Nombre total de VMs - LATEST 30j |
| Field | `summary_number_running_vms` | Nombre de VMs actives - LATEST 30j |
| Field | `vmop_inventoryChange_numCreate_latest` | VMs créées - SUM 30j |
| Field | `vmop_inventoryChange_numDestroy_latest` | VMs détruites - SUM 30j |

### 8.2 vm_lifecycle

Collecté par : `aria.py` (Aria Operations)

| Type | Clé | Description |
|------|-----|-------------|
| Tag | `datacenter` | Nom du datacenter/ressource |
| Tag | `name` | Nom de la VM |
| Tag | `id` | Identifiant de la VM |
| Field | `is_deleted` | Booléen : VM détruite |
| Field | `created_at` | Timestamp de création (int, null si indisponible) |
| Field | `destroyed_at` | Timestamp de destruction (int, null si indisponible) |

### 8.3 datastore_usage

Collecté par : `vsphere.py` (vSphere)

| Type | Clé | Description |
|------|-----|-------------|
| Tag | `datastore_data` | Nom du datastore |
| Tag | `type` | Type (VMFS, NFS, etc.) |
| Tag | `datastore_folder` | Dossier contenant le datastore |
| Tag | `datacenter` | Nom du datacenter (DC_NAME) |
| Field | `total_capacity` | Capacité totale en GB (float, 2 déc.) |
| Field | `free_space` | Espace libre en GB (float, 2 déc.) |
| Field | `space_use` | Espace utilisé en GB (float, 2 déc.) |
| Field | `percent_use` | Pourcentage d'utilisation (float, 2 déc.) |

### 8.4 powerstore_performance

Collecté par : `powerstore.py` (Dell PowerStore)

| Type | Clé | Description |
|------|-----|-------------|
| Tag | `datacenter` | Nom du datacenter (DC_NAME) |
| Tag | `cluster_id` | ID du cluster |
| Tag | `node_id` | ID du node |
| Tag | `appliance_id` | ID de l'appliance |
| Tag | `response_definition` | Définition de la métrique API |
| Tag | `entity` | Type d'entité (espace/perf cluster/node/appliance) |
| Fields | Dynamiques | Métriques API PowerStore (performance et espace) |

### 8.5 unity_metrics

Collecté par : `unity.py` (Dell Unity)

| Type | Clé | Description |
|------|-----|-------------|
| Tag | `datacenter` | Nom du datacenter (DC_NAME) |
| Tag | `name` | Nom de la ressource |
| Tag | `id` | ID Unity de la ressource |
| Field | `model` | Modèle (system uniquement) |
| Field | `serialNumber` | Numéro de série (system uniquement) |
| Fields | Dynamiques | Métriques spécifiques par type de ressource |

---

## 9. Grafana et visualisation

> Guide utilisateur complet (dashboards, export CSV, troubleshooting) : [GRAFANA.md](GRAFANA.md)

### 9.1 Datasource

**Nom :** `InfluxDB-v3-SQL`
- Type : InfluxDB
- URL : `http://influxdb3:8181`
- Version : SQL
- Base de données : `${INFLUXDB_BUCKET}` ( interpolation d'environnement)
- Default : Oui

### 9.2 Dashboards

#### Dashboard 01 - Infrastructure Overview
- **UID :** `4e00646f-67a1-4727-8ef4-47c94b3b2dec`
- **Variables :** `$dc1`, `$dc2` (cachés, datacenters tirés de `vm_lifecycle`)
- **Panels :** Top 10 Datastores, Datastore Details, Unity pools, PowerStore clusters/nodes/appliances, Total VMs (par datacenter), VMs Created (30d), VMs Destroyed (30d), Datastores, Total Capacity, Avg Utilization
- **Requêtes VM :** basées sur `vm_lifecycle` (les mesures `vm_inventory` et `system_metrics` ont été remplacées)

#### Dashboard 02 - VMware vSphere - Datastores
- **UID :** `197d43f6-8286-488d-8972-d5be64d703db`
- **Variables :** `$datacenter`, `$type`
- **Panels :** Datastore Inventory (tableau), Usage Over Time (timeseries), Current Usage (bargauge), Capacity Distribution (piechart), Datastores > 80% Full (alerte)

#### Dashboard 03 - Dell Storage Systems
- **UID :** `f865fbe1-6511-4713-9736-2d22837bfb89`
- **Variables :** `$datacenter`, `$entity` (type d'entité PowerStore)
- **Sections :** Dell Unity Storage (SP utilisation, pools, LUNs, filesystems) et Dell PowerStore (capacité physique, métriques de performance)

#### Dashboard 04 - VMware Aria Operations
- **UID :** `fba67df3-e282-48ec-8c45-b0b7e6579bec`
- **Variables :** `$datacenter`, `$name` (nom du cluster)
- **Panels :** VMs totales, VMs créées/détruites, VM lifecycle (tableau avec window function), VM Operations Timeline, CPU/Memory usage

---

## 10. Gestion des secrets

### Principe

Les credentials sont gérés via **Docker Secrets** et montés dans les conteneurs au chemin `/run/secrets/<nom_du_secret>`.

### Fichiers de secrets

| Secret | Fichier source | Conteneur monté | Variable d'env |
|--------|---------------|------------------|----------------|
| `aria_s` | `./secrets/aria.txt` | `/run/secrets/aria_s` | `NAME=aria_s` (aria_collector) |
| `one_s` | `./secrets/one.txt` | `/run/secrets/one_s` | `NAME=one_s` (collector1) |
| `two_s` | `./secrets/two.txt` | `/run/secrets/two_s` | `NAME=two_s` (collector2) |

### Format des fichiers

```
# Fichier aria.txt
ARIA_HOST=192.168.1.100
ARIA_USER=administrator@vsphere.local
ARIA_AUTH_SOURCE=vsphere.local
ARIA_PASSWD=motdepasse

# Fichier one.txt / two.txt
VCENTER_HOST=192.168.1.10
VCENTER_USER=administrator@vsphere.local
VCENTER_PASSWD=motdepasse
UNITY_HOST=192.168.1.20
UNITY_USER=admin
UNITY_PASSWD=motdepasse
POWERSTORE_HOST=192.168.1.30
POWERSTORE_USER=admin
POWERSTORE_PASSWD=motdepasse
```

### Lecture dans le code

```python
from utils import get_secrets

secrets = get_secrets(os.getenv("NAME"))
# NAME est défini par conteneur (one_s, two_s, ou aria_s)
```

---

## 11. Variables d'environnement

### Fichier `.env` (racine du projet)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `INFLUXDB_HTTP_PORT` | Port HTTP InfluxDB | `8181` |
| `INFLUXDB_HOST` | Hostname InfluxDB (interne Docker) | `influxdb3` |
| `INFLUXDB_TOKEN` | Token API InfluxDB | `apiv3_...` |
| `INFLUXDB_BUCKET` | Nom de la base de données | `infra` |
| `INFLUXDB_ORG` | Organisation InfluxDB | `local_org` |
| `INFLUXDB_NODE_ID` | ID du nœud InfluxDB | `node0` |
| `ADMIN` | Identifiant Grafana | `grafana` |
| `PASSW` | Mot de passe Grafana | `grafana` |
| `ARIA_RESOURCE_ID1` | ID ressource Aria pour collector1 | |
| `ARIA_RESOURCE_ID2` | ID ressource Aria pour collector2 | |
| `MAP_ID1` | ID mapping Aria pour collector1 | |
| `MAP_ID2` | ID mapping Aria pour collector2 | |
| `DS_FOLDER1` | Dossier datastore pour collector1 | `Datacenter1` |
| `DC_NAME1` | Nom datacenter pour collector1 | `DC-West` |
| `DS_FOLDER2` | Dossier datastore pour collector2 | `Datacenter2` |
| `DC_NAME2` | Nom datacenter pour collector2 | `DC-East` |

---

## 12. Commandes Makefile

| Commande | Description | Détail |
|----------|-------------|--------|
| `make start` / `make s` | Démarrer le stack | `docker compose up -d` |
| `make stop` / `make st` | Arrêter le stack | `docker compose down` |
| `make clean` | Nettoyer (volumes inclus) | `down` + suppression `influxdb_data`, `grafana_data` |
| `make aria` | Exécuter Aria sur `aria_collector` | `docker exec aria_collector aria` |
| `make one` | Exécuter tous les collecteurs sur `collector1` | `docker exec collector1 all` |
| `make two` | Exécuter tous les collecteurs sur `collector2` | `docker exec collector2 all` |
| `make o_vsphere` | Exécuter vsphere sur `collector1` | `docker exec collector1 vsphere` |
| `make o_powerstore` | Exécuter powerstore sur `collector1` | `docker exec collector1 powerstore` |
| `make o_unity` | Exécuter unity sur `collector1` | `docker exec collector1 unity` |
| `make t_vsphere` | Exécuter vsphere sur `collector2` | `docker exec collector2 vsphere` |
| `make t_powerstore` | Exécuter powerstore sur `collector2` | `docker exec collector2 powerstore` |
| `make t_unity` | Exécuter unity sur `collector2` | `docker exec collector2 unity` |
| `make collector` | Exécuter tous les collecteurs | `aria` + `one` + `two` |
| `make run` | Démarrer + collecter | `start` + `collector` |

---

## 13. Dockerfile et entrypoint

### Dockerfile

```dockerfile
FROM alpine:latest
RUN apk add --no-cache python3 py3-pip
WORKDIR /app
COPY app/ .
COPY tools/ .
RUN pip install -r requirements.txt
RUN chmod +x tools/entrypoint.sh
ENTRYPOINT ["entrypoint"]
CMD ["tail", "-f", "/var/log/logger.log"]
```

**Image :** Alpine Linux minimaliste avec Python 3 et pip.
**Build context :** `./requirements/collector`

### entrypoint.sh

Le script d'entrée crée des liens symboliques dans `/usr/local/bin/` pour chaque commande de collecte :

| Lien | Script cible | Action |
|------|-------------|--------|
| `/usr/local/bin/all` | `all.sh` | Exécute powerstore + unity + vsphere |
| `/usr/local/bin/aria` | `aria.sh` | Exécute `aria.py` |
| `/usr/local/bin/powerstore` | `powerstore.sh` | Exécute `powerstore.py` |
| `/usr/local/bin/unity` | `unity.sh` | Exécute `unity.py` |
| `/usr/local/bin/vsphere` | `vsphere.sh` | Exécute `vsphere.py` |

Chaque script shell redirige la sortie vers `/var/log/logger.log`.

### Journal des collectes

Tous les logs sont dirigés vers `/var/log/logger.log`. Consulter avec :

```bash
docker logs -f aria_collector
docker logs -f collector1
docker logs -f collector2
```

---

## 14. Problèmes connus


### 14.1 Certificats auto-signés

Les cibles de collecte (vCenter, Aria, PowerStore, Unity) utilisent fréquemment des certificats auto-signés. Le code désactive les avertissements SSL :

- **Aria, PowerStore, Unity :** `urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)` + `verify=False`
- **vSphere :** `ssl._create_unverified_context()` via pyvmomi

---

## 15. Sécurité

### 15.1 Secrets

- Les credentials ne doivent **jamais** être commités dans le dépôt
- Les fichiers `.txt` de secrets sont exclus du dépôt git
- Seuls les fichiers `.example` sont versionnés
- Docker Secrets montent les credentials en mémoire (`/run/secrets/`)

### 15.2 InfluxDB

- L'authentification est désactivée (`--without-auth`)
- Recommandation : activer l'authentification pour les environnements de production

### 15.3 SSL/TLS

- Les connexions aux sources de données utilisent `verify=False`
- Recommandation : configurer les certificats racines pour les environnements de production

### 15.4 Réseau

- InfluxDB est exposé sur le port 8181 (accessible depuis l'hôte)
- Grafana est exposé sur le port 3000
- Recommandation : restreindre l'accès réseau aux ports exposés

### 15.5 Licence

Projet sous licence **Apache 2.0**.
