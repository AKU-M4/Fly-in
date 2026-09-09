UV = uv

# Detect all root-level python files while excluding hidden folders and .venv
PY_FILES = $(wildcard *.py)

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) sync

run:
	python3 main.py $(MAP)

debug:
	$(UV) run python -m pdb main.py maps/map_easy.txt

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache .venv

lint:
	$(UV) run flake8 --exclude=.venv,__pycache__ $(PY_FILES)
	$(UV) run mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude '^\.venv' $(PY_FILES)

lint-strict:
	$(UV) run flake8 --exclude=.venv,__pycache__ $(PY_FILES)
	$(UV) run mypy --strict --exclude '^\.venv' $(PY_FILES)