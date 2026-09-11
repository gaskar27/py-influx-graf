# main.py

> **Navigation :** [README](../../README.md) · [Index de la documentation](../README.md) · [Documentation technique](../DOCUMENTATION_TECHNIQUE.md) · [Grafana](../GRAFANA.md)

Orchestrateur d'execution des collecteurs pour `collector1` et `collector2`.

## Position

`requirements/collector/app/main.py`

## Vue d'ensemble

Script d'entree point qui execute sequentiellement les trois collecteurs de metriques d'infrastructure : PowerStore, Unity et vSphere. Utilise par les services `collector1` et `collector2` dans le `compose.yaml`.

## Scripts executes

| Ordre | Script | Description |
|---|---|---|
| 1 | `powerstore.py` | Collecte metriques Dell PowerStore |
| 2 | `unity.py` | Collecte metriques Dell Unity |
| 3 | `vsphere.py` | Collecte metriques datastores vSphere |

## Comportement

- Parcourt la liste `scripts = ["powerstore.py", "unity.py", "vsphere.py"]`.
- Execute chaque script via `subprocess.run(["python3", script])`.
- Affiche un message de demarrage et de fin.

## Execution

```bash
python3 main.py
```

Ou via le Makefile :

```bash
make one    # Execute dans collector1
make two    # Execute dans collector2
```

## Notes

- L'execution est **sequentielle** : chaque script termine avant le demarrage du suivant.
- Chaque script lit ses propres secrets via `get_secrets(NAME)` ou `get_secrets("one_s")` / `get_secrets("two_s")` selon le conteneur.
- Le script `aria.py` n'est **pas** inclus ici ; il est execute separement via `make aria` dans le conteneur `aria_collector`.

## Scripts documentés

- [powerstore.py](powerstore.md) — métriques Dell PowerStore
- [unity.py](unity.md) — métriques Dell Unity
- [vsphere.py](vsphere.md) — utilisation des datastores vSphere
