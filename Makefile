.ONESHELL:
.DEFAULT_GOAL: all

py := python3 -m
source_dir := rarible_marketplace_indexer
unit_tests_dir := tests

install:
	$(py) pip install --upgrade --force-reinstall -r requirements.txt

install_tests:
	$(py) pip install --upgrade --force-reinstall -r requirements.tests.txt

isort:
	$(py) isort $(source_dir) $(unit_tests_dir)

ssort:
	$(py) ssort $(source_dir) $(unit_tests_dir)

black:
	$(py) black $(source_dir) $(unit_tests_dir)

flake:
	$(py) flakeheaven lint $(source_dir) $(unit_tests_dir)

mypy:
	$(py) mypy $(source_dir) $(unit_tests_dir)

test:
	$(py) pytest $(source_dir) $(unit_tests_dir)

lint: isort ssort black flake

prepare_services_dev:
	docker-compose -f docker-compose.dev.yml up -d --remove-orphans db hasura kafdrop kafka zookeeper prometheus grafana

prepare_services_testnet:
	docker-compose -f docker-compose.testnet.yml up -d --remove-orphans db hasura kafdrop kafka zookeeper prometheus grafana

prepare_services_prod:
	docker-compose -f docker-compose.prod.yml up -d --remove-orphans db hasura kafdrop kafka zookeeper prometheus grafana

up_dev: prepare_services_dev
	docker-compose -f docker-compose.dev.yml up --build --remove-orphans --force-recreate --no-deps --abort-on-container-exit indexer-rarible indexer-tezos indexer-metadata

up_test: prepare_services_testnet
	docker-compose -f docker-compose.testnet.yml up --build --remove-orphans --force-recreate --no-deps --abort-on-container-exit indexer-rarible indexer-tezos indexer-metadata

up_prod: prepare_services_prod
	docker-compose -f docker-compose.prod.yml up --build --remove-orphans --force-recreate --no-deps --abort-on-container-exit indexer-rarible indexer-tezos indexer-metadata

down_dev:
	docker-compose -f docker-compose.dev.yml down --volumes

down_test:
	docker-compose -f docker-compose.testnet.yml down --volumes

down_prod:
	docker-compose -f docker-compose.prod.yml down --volumes

build:
	docker build . -t rarible_indexer:dev --platform linux/amd64

run_dev: prepare_services_dev build up_dev

run_testnet: prepare_services_testnet build up_test

run_prod: prepare_services_prod build up_prod

reset: down_dev down_test down_prod