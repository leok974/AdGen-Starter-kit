COMPOSE_FILE=adgen/docker-compose.dev.yml
COMPOSE=docker compose

up:
	$(COMPOSE) -f $(COMPOSE_FILE) build
	$(COMPOSE) -f $(COMPOSE_FILE) up -d

down:
	$(COMPOSE) -f $(COMPOSE_FILE) down

logs:
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f --tail=200
