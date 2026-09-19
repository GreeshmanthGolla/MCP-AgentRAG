.PHONY: install data test demo web serve-mcp eval clean

VENV = .venv
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip
PYTEST = $(VENV)/Scripts/pytest

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

data:
	$(PYTHON) scripts/generate_synthetic_data.py

test:
	$(PYTEST) -v tests/

demo:
	$(PYTHON) run.py demo

web:
	$(PYTHON) run.py web

serve-mcp:
	$(PYTHON) run.py serve-mcp

eval:
	$(PYTHON) run.py eval

clean:
	rm -rf __pycache__ .pytest_cache data/storage/*.sqlite
