.ONESHELL:
.DEFAULT_GOAL: all

py := poetry run
source_dir := rarible_marketplace_indexer
unit_tests_dir := tests

install:
	poetry install `if [ "${DEV}" = "0" ]; then echo "--no-dev"; fi`

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

prepare_services:
	docker-compose up -d --remove-orphans db hasura kafdrop kafka zookeeper prometheus grafana

up: prepare_services
	docker-compose up --build --remove-orphans --force-recreate --no-deps --abort-on-container-exit indexer-rarible indexer-tezos

down:
	docker-compose down --volumes

build:
	docker build . -t rarible_indexer:dev --platform linux/amd64

build_and_run: build up

reset: down prepare_services