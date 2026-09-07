.PHONY: start s run stop st clean help

.DEFAULT_GOAL := help

start s:
	docker compose up -d

aria:
	docker exec aria_collector aria

one:
	docker exec collector1 all

o_vsphere:
	docker exec collector1 vsphere

o_powerstore:
	docker exec collector1 powerstore

o_unity:
	docker exec collector1 unity

two:
	docker exec collector2 all

t_vsphere:
	docker exec collector2 vsphere

t_powerstore:
	docker exec collector2 powerstore

t_unity:
	docker exec collector2 unity

collector: aria one two

run:
	$(MAKE) start && $(MAKE) collector

stop st:
	docker compose down

clean: stop
	docker volume rm influxdb_data grafana_data

help:
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commandes disponibles :"
	@echo "  start, s   : Démarrer l'application"
	@echo "  run        : Démarrer l'application et exécuter le collecteur"
	@echo "  stop, st   : Arrêter l'application"
	@echo "  clean      : Supprimer les données"
	@echo "  help       : Afficher ce message d'aide"
