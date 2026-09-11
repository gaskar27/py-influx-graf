# utils.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Utilitaires partages par les collecteurs.

## Position

`requirements/collector/app/utils.py`

## Vue d'ensemble

Module utilitaire contenant la fonction `get_secrets()` utilisee par tous les collecteurs pour lire les credentials depuis les fichiers Docker secrets montes dans le conteneur.

## Fonction `get_secrets(secret_file)`

### Signature

```python
def get_secrets(secret_file) -> dict | None
```

### Parametre

| Parametre | Type | Description |
|---|---|---|
| `secret_file` | `str` | Nom du fichier secret (sans le chemin). Ex: `aria_s`, `one_s`, `two_s`. |

### Comportement

1. Construit le chemin : `/run/secrets/{secret_file}`.
2. Verifie que le fichier existe.
3. Lit le fichier ligne par ligne :
   - Ignore les lignes vides et les commentaires (commencant par `#`).
   - Parse les lignes au format `cle=valeur` (seulement sur le premier `=`).
4. Retourne un dictionnaire `{cle: valeur}` ou `None` si le fichier est vide/inexistant.

### Exemple de fichier secret

```
# Fichier: /run/secrets/aria_s
ARIA_HOST=vcenter-aria.example.com
ARIA_USER=admin@vsphere.local
ARIA_PASSWD=mot_de_passe
ARIA_AUTH_SOURCE=vsphere.local
```

### Retour

```python
{
    "ARIA_HOST": "vcenter-aria.example.com",
    "ARIA_USER": "admin@vsphere.local",
    "ARIA_PASSWD": "mot_de_passe",
    "ARIA_AUTH_SOURCE": "vsphere.local"
}
```

Ou `None` si le fichier n'existe pas ou est vide.

## Utilisation dans les collecteurs

```python
from utils import get_secrets

s = get_secrets("aria_s")
host = s.get("ARIA_HOST")
```

Chaque collecteur lit son fichier secret via `get_secrets(NAME)` :

| Collecteur | Secret | Variables lues |
|---|---|---|
| [aria.py](aria.md) | `aria_s` | `ARIA_HOST`, `ARIA_USER`, `ARIA_PASSWD`, `ARIA_AUTH_SOURCE` |
| [vsphere.py](vsphere.md) | `one_s` / `two_s` | `VCENTER_HOST`, `VCENTER_USER`, `VCENTER_PASSWD` |
| [powerstore.py](powerstore.md) | `one_s` / `two_s` | `POWERSTORE_HOST`, `POWERSTORE_USER`, `POWERSTORE_PASSWD` |
| [unity.py](unity.md) | `one_s` / `two_s` | `UNITY_HOST`, `UNITY_USER`, `UNITY_PASSWD` |

`NAME` est défini par conteneur dans le `compose.yaml` : `aria_s` (aria_collector), `one_s` (collector1), `two_s` (collector2).
