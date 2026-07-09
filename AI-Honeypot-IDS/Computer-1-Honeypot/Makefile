# =============================================================================
# Computer 1 — Honeypot Makefile
# Convenience targets for building, starting, stopping, and inspecting the
# honeypot. Run `make help` to list targets.
# =============================================================================
.PHONY: help build up down status logs logs-f restart clean health seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

build: ## Build (or rebuild) all container images
	docker compose build

up: ## Start all honeypot containers + filebeat
	docker compose up -d
	@echo ""
	@echo "Waiting for health checks..."
	@sleep 8
	@$(MAKE) --no-print-directory status

down: ## Stop and remove containers (keeps images)
	docker compose down

restart: down up ## Restart everything

status: ## Show container status table
	@echo "================ HONEYPOT CONTAINER STATUS ================"
	@docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}"
	@echo "==========================================================="

logs: ## Tail logs from all containers (Ctrl-C to exit)
	docker compose logs -f --tail=50

logs-f: logs

health: ## Run the HTTP healthcheck script against every container
	@./scripts/healthcheck.sh

seed: ## Generate benign baseline traffic (for ML normal-class samples)
	@./scripts/seed-traffic.sh

clean: ## Stop + remove containers, volumes, dangling images
	docker compose down -v
	docker image prune -f
