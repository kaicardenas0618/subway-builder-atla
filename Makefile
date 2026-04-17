PYTHON ?= python3

.PHONY: prod dev serve install test

prod:
	$(PYTHON) -m src.main build --mode prod

dev:
	$(PYTHON) -m src.main build --mode dev

serve:
	$(PYTHON) -m src.main serve

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -v
