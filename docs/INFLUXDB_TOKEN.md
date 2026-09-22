# Gestion des tokens InfluxDB

> **Navigation :** [README](../README.md) · [Index de la documentation](README.md) · [Documentation technique](DOCUMENTATION_TECHNIQUE.md) · [Guide utilisateur Grafana](GRAFANA.md)

Depuis l'activation de l'authentification (option `--admin-token-file` dans `compose.yaml`), le service `influxdb3` exige un **token admin** pour accepter toute requête (écriture des collecteurs, datasource Grafana, création de base de données).

Ce guide détaille la génération et la gestion de ce token, adapté au setup Docker Compose de ce projet.

---

## Étape 1 : Générer le fichier token offline depuis l'image

Générer un **operator token** (token admin de secours) en mode offline, directement sur la machine hôte. La génération passe par un dossier temporaire `tokens/` auquel le conteneur doit pouvoir écrire :

```bash
# Pull l'image si elle n'est pas encore présente
docker pull influxdb:3.9.3-core
```

```bash
mkdir -p tokens
chmod 777 tokens

docker run --rm \
  -v $(pwd)/tokens:/tokens \
  influxdb:3.9.3-core \
  influxdb3 create token --admin \
    --name admin \
    --offline \
    --output-file /tokens/admin_token.json

mv tokens/admin_token.json secrets/admin_token.json
rm -rf tokens
```

> Cette commande crée le fichier `./secrets/admin_token.json` contenant l'operator token. C'est ce fichier que les services Docker attendent : il est monté en secret sur `/run/secrets/admin_token` ([Générer un token offline](https://docs.influxdata.com/influxdb3/core/reference/cli/influxdb3/create/token/admin/#generate-an-offline-admin-token)).

Le fichier étant référencé dans `.gitignore`, il ne sera jamais commité.

## Étape 2 : Démarrer le service

```bash
make influx
```

Le healthcheck du conteneur lit l'operator token depuis le secret pour vérifier l'état du service.

## Étape 3 : Créer un named admin token pour usage quotidien

Une fois le serveur démarré, utilisez l'**operator token** (contenu dans `admin_token.json`) pour créer un **named admin token** :

```bash
docker exec -it influxdb3 influxdb3 create token --admin \
  --token OPERATOR_TOKEN \
  --name token-app \
  --expiry 90d
```

Renseigner ensuite la valeur retournée dans la variable `INFLUXDB_TOKEN` du fichier `.env` — elle est utilisée par les collecteurs (`influx_writer.py`) et par la datasource Grafana.

Note: `--expiry` n'est pas obligatoire. S'il n'est pas spécifié, le token n'expirera jamais.

> L'idée est de **ne jamais utiliser directement l'operator token** dans vos applications — réservez-le uniquement pour créer/renouveler des named admin tokens ([Manage admin tokens](https://docs.influxdata.com/influxdb3/core/admin/tokens/admin/)).

## Étape 4 : Gérer le renouvellement des named tokens expirés

Quand un named admin token expire (erreur `401 Unauthorized`), recréez-en un nouveau avec l'operator token :

```bash
# Supprimer l'ancien token expiré
docker exec -it influxdb3 influxdb3 delete token --token-name "token-app"

# Créer un nouveau token
docker exec -it influxdb3 influxdb3 create token --admin \
  --token OPERATOR_TOKEN \
  --name token-app \
  --expiry 90d
```

Puis mettre à jour `INFLUXDB_TOKEN` dans `.env` et redémarrer les services concernés :

```bash
make stop && make start
```

([Manage admin tokens](https://docs.influxdata.com/influxdb3/core/admin/tokens/admin/))

---

## Résumé des bonnes pratiques

| Token | Rôle | Expiration |
|---|---|---|
| **Operator token** | Stocké en lieu sûr (`admin_token.json`), utilisé uniquement pour gérer les autres tokens | Jamais |
| **Named admin token** | Utilisé par vos applications (`INFLUXDB_TOKEN`) | À définir (ex : `90d`) |

> **Important :** Stockez l'operator token dans un gestionnaire de secrets (ex : Vault, AWS Secrets Manager) — c'est votre seul recours en cas d'expiration ou de perte d'un named admin token.
