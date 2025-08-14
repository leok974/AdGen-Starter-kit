# Makefile for development and Docker commands

.PHONY: fmt lint type test up down logs

# Development commands
fmt:
	black api

lint:
	ruff check api

type:
	mypy api

test:
	pytest -q api/tests

# Docker commands
COMPOSE_FILE := docker-compose.dev.yml

up:
	@echo "Starting up services..."
	docker compose -f $(COMPOSE_FILE) build --pull=never
	docker compose -f $(COMPOSE_FILE) up -d

down:
	@echo "Stopping services..."
	docker compose -f $(COMPOSE_FILE) down

logs:
	@echo "Tailing logs..."
	docker compose -f $(COMPOSE_FILE) logs -f --tail=200
