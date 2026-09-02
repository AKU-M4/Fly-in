UV = uv

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) sync

run:
	$(UV) run python -m src maps/hard/02_capacity_hell.txt

debug:
	$(UV) run python -m pdb main.py maps/map_easy.txt

clean:
	rm -rf __pycache__ src/__pycache__ .mypy_cache .pytest_cache .venv

lint:
	$(UV) run flake8 src/ main.py
	$(UV) run mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs src/ main.py

lint-strict:
	$(UV) run flake8 src/ main.py
	$(UV) run mypy --strict src/ main.py