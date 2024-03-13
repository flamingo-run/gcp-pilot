setup:
	@pip install -U pip poetry

dependencies:
	@make setup
	@poetry install --no-root --all-extras

update:
	@poetry update

test:
	@make check
	@make lint
	@make unit

check:
	@poetry check

lint:
	@echo "Checking code style ..."
	poetry run ruff format --check .
	poetry run ruff check .

style:
	@echo "Applying code style ..."
	poetry run ruff format .
	poetry run ruff check . --fix

unit:
	@echo "Running unit tests ..."
	@poetry run pytest

clean:
	@rm -rf .coverage coverage.xml dist/ build/ *.egg-info/

publish:
	@make clean
	@printf "\nPublishing lib"
	@make setup
	@poetry config pypi-token.pypi $(PYPI_API_TOKEN)
	@poetry publish --build
	@make clean


.PHONY: setup dependencies update test check lint clean publish
