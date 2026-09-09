# py-influx-graf

Stack Docker d'infrastructure monitoring combinant InfluxDB 3, Grafana et des collecteurs Python personnalisés pour VMware Aria Operations, vSphere, Dell PowerStore et Dell Unity.

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0
- [Make](https://www.gnu.org/software/make/) (optionnel, pour les commandes simplifiées)

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/gaskar27/py-influx-graf.git
cd py-influx-graf
```

### 2. Configurer l'environnement

Copier le fichier d'environnement et renseigner les valeurs :

```bash
cp .env.example .env
```

Modifier `.env` :

| Variable | Description |
|---|---|
| `INFLUXDB_TOKEN` | Token d'authentification InfluxDB (générer un token via `influxctl` ou la CLI) |
| `INFLUXDB_BUCKET` | Nom de la base de données (défaut : `local_system`) |
| `ADMIN` | Utilisateur admin Grafana |
| `PASSW` | Mot de passe admin Grafana |

### 3. Configurer les secrets

Créer les fichiers de secrets à partir des exemples :

```bash
cp secrets/aria.txt.example secrets/aria.txt
cp secrets/one.txt.example secrets/one.txt
cp secrets/two.txt.example secrets/two.txt
```

Renseigner chaque fichier avec les identifiants des infrastructure cibles :

**`secrets/aria.txt`** — VMware Aria Operations :
```
ARIA_HOST=192.168.x.x
ARIA_USER=utilisateur
ARIA_AUTH_SOURCE=source
ARIA_PASSWD=motdepasse
```

**`secrets/one.txt`** / **`secrets/two.txt`** — vSphere + Dell Unity + Dell PowerStore :
```
VCENTER_HOST=192.168.x.x
VCENTER_USER=utilisateur
VCENTER_PASSWD=motdepasse
UNITY_HOST=192.168.x.x
UNITY_USER=utilisateur
UNITY_PASSWD=motdepasse
POWERSTORE_HOST=192.168.x.x
POWERSTORE_USER=utilisateur
POWERSTORE_PASSWD=motdepasse
```

### 4. Lancer le stack

```bash
make start
```

Ou directement démarrer + collecter les métriques :

```bash
make run
```

## Quickstart

```bash
# 1. Préparer la config
cp .env.example .env
cp secrets/aria.txt.example secrets/aria.txt
cp secrets/one.txt.example secrets/one.txt
cp secrets/two.txt.example secrets/two.txt
```
```bash
# 2. Éditer les fichiers .env et secrets/ avec vos identifiants

# 3. Démarrer et collecter
make run
```

Grafana est accessible sur `http://localhost:3000` avec les identifiants définis dans `.env`.

## Commandes disponibles

| Commande | Description |
|---|---|
| `make start` / `make s` | Démarrer le stack |
| `make run` | Démarrer + exécuter tous les collecteurs |
| `make stop` / `make st` | Arrêter le stack |
| `make clean` | Arrêter et supprimer les volumes de données |
| `make collector` | Exécuter tous les collecteurs (aria + collector1 + collector2) |
| `make aria` | Exécuter le collecteur Aria |
| `make one` / `make two` | Exécuter tous les collecteurs sur collector1/collector2 |
| `make o_vsphere` | Exécuter vsphere sur collector1 |
| `make o_powerstore` | Exécuter powerstore sur collector1 |
| `make o_unity` | Exécuter unity sur collector1 |
| `make t_vsphere` | Exécuter vsphere sur collector2 |
| `make t_powerstore` | Exécuter powerstore sur collector2 |
| `make t_unity` | Exécuter unity sur collector2 |

## Dashboard Grafana

Quatre dashboards sont provisionnés automatiquement :

1. **Infrastructure Overview** — Vue d'ensemble de l'infrastructure
2. **VMware vSphere - Datastores** — Utilisation et capacité des datastores
3. **Dell Storage Systems** — Métriques Unity et PowerStore
4. **VMware Aria Operations** — Métriques clusters et cycle de vie des VMs
