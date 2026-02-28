COMPOSE_FILE := infra/docker/docker-compose.yml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

.PHONY: docker-build docker-config docker-up docker-up-frontend docker-down docker-logs docker-ps

docker-build:
	$(DOCKER_COMPOSE) build

docker-config:
	$(DOCKER_COMPOSE) config

docker-up:
	$(DOCKER_COMPOSE) up --build

docker-up-frontend:
	$(DOCKER_COMPOSE) --profile frontend up --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

docker-ps:
	$(DOCKER_COMPOSE) ps
