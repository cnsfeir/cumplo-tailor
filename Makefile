include .env
export

.PHONY: \
  start \
  build \
  down \
  login \
  update_common

# Activates the project configuration and logs in to gcloud
login:
	@gcloud config configurations activate $(PROJECT_ID)
	@gcloud auth application-default login

# Runs linters
.PHONY: lint
lint:
	@ruff check --fix
	@ruff format
	@mypy --config-file pyproject.toml .

build:
	@docker-compose build cumplo-tailor --build-arg CUMPLO_PYPI_BASE64_KEY=`base64 -i cumplo-pypi-credentials.json`

start:
	@docker-compose up -d cumplo-tailor

down:
	@docker-compose down

update_common:
	@rm -rf .venv
	@poetry cache clear --no-interaction --all cumplo-pypi
	@poetry update
