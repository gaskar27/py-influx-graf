.PHONY: start s stop st down d help

.DEFAULT_GOAL := help

start s:
	docker compose up -d

stop st:
	docker compose down

down d:
	docker compose down -v

help:
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commandes disponibles :"
	@echo "  start, s   : Démarrer l'application"
	@echo "  stop, st   : Arrêter l'application"
	@echo "  down, d    : Arrêter l'application et supprimer les données"
	@echo "  help       : Afficher ce message d'aide"
