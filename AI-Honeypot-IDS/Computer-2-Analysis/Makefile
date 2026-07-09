# Computer 2 — ELK + ML Makefile
.PHONY: help elk-up elk-down elk-status elk-logs kibana ingest features train evaluate stats all-models full-pipeline

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-15s\033[0m %s\n",$$1,$$2}'

elk-up: ## Start ELK stack
	docker compose -f elk/docker-compose-elk.yml up -d
	@echo "[+] Waiting for Elasticsearch..."
	@for i in $$(seq 1 30); do \
	  curl -fsS http://127.0.0.1:9200/_cluster/health >/dev/null 2>&1 && break; \
	  sleep 2; \
	done
	@echo "[+] ELK up. Kibana: http://127.0.0.1:5601"

elk-down: ## Stop ELK
	docker compose -f elk/docker-compose-elk.yml down

elk-status: ## ELK container status
	docker compose -f elk/docker-compose-elk.yml ps

elk-logs: ## Tail ELK logs
	docker compose -f elk/docker-compose-elk.yml logs -f --tail=50

kibana: ## Open Kibana in default browser
	@xdg-open http://127.0.0.1:5601 || open http://127.0.0.1:5601 || echo "open http://192.168.1.20:5601"

dashboards: ## Load Kibana dashboards
	@./dashboards/setup_dashboards.sh

ingest: ## Pull logs from ES → data/raw.parquet
	cd ml && python src/01_ingest.py

features: ## Build features → data/features.parquet
	cd ml && python src/02_features.py

train: ## Train all 6 models with CV
	cd ml && python src/03_train.py

evaluate: ## Evaluate + confusion matrix + ROC + copy best model
	cd ml && python src/04_evaluate.py

stats: ## Dataset EDA summary
	cd ml && python src/05_dataset_stats.py

all-models: ingest features train evaluate stats ## Full ML pipeline end-to-end

full-pipeline: elk-up dashboards all-models ## ELK up + dashboards + full ML pipeline
