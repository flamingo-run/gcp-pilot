dependencies:
	@uv sync --all-extras

update:
	@uv lock --upgrade

test:
	@make check
	@make lint
	@make unit

check:
	@uv lock --locked

lint:
	@echo "Checking code style ..."
	uv run ruff format --check .
	uv run ruff check .

style:
	@echo "Applying code style ..."
	uv run ruff format .
	uv run ruff check . --fix --unsafe-fixes

unit:
	@echo "Running unit tests ..."
	@uv run pytest

clean:
	@rm -rf .coverage coverage.xml dist/ build/ *.egg-info/

publish:
	@make clean
	@printf "\nPublishing lib"
	@uv build
	@uv publish --token $(PYPI_API_TOKEN)
	@make clean


.PHONY: setup dependencies update test check lint clean publish
