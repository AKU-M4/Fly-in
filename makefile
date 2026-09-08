UV = uv

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) sync

run:
	python3 main.py "maps/medium/03_priority_puzzle.txt"

debug:
	$(UV) run python -m pdb main.py maps/map_easy.txt

clean:
	rm -rf __pycache__ __pycache__ .mypy_cache .pytest_cache .venv

lint:
	$(UV) run flake8
	$(UV) run mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs src/ main.py

lint-strict:
	$(UV) run flake8
	$(UV) run mypy --strict