install:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e ".[dev]"

run:
	.venv/bin/python -m fly_in.main

debug:
	.venv/bin/python -m pdb -m fly_in.main

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -prune -exec rm -rf {} +

lint:
	.venv/bin/flake8 . --exclude=.venv,venv
	.venv/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	.venv/bin/flake8 . --exclude=.venv,venv
	.venv/bin/mypy . --strict

.PHONY: install run debug clean lint lint-strict