# Makefile for managing the Docker development environment

# Use this docker-compose file
COMPOSE_FILE := adgen/docker-compose.dev.yml

.PHONY: up down logs

up:
	@echo "Starting up services..."
	sudo docker compose -f $(COMPOSE_FILE) build
	sudo docker compose -f $(COMPOSE_FILE) up -d

down:
	@echo "Stopping services..."
	sudo docker compose -f $(COMPOSE_FILE) down

logs:
	@echo "Tailing logs..."
	sudo docker compose -f $(COMPOSE_FILE) logs -f
