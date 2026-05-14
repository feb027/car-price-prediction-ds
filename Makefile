PYTHON ?= python3

.PHONY: validate dataset smoke test pycompile run

validate: dataset pycompile smoke test

dataset:
	$(PYTHON) scripts/validate_dataset.py

pycompile:
	$(PYTHON) -m py_compile scripts/*.py src/*.py api/*.py

smoke:
	$(PYTHON) scripts/smoke_app_pipeline.py

test:
	$(PYTHON) -m pytest -q

run:
	$(PYTHON) -m uvicorn api.main:app --host 127.0.0.1 --port 8516
