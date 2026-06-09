PYTHON ?= python3

.PHONY: help verify test guard vintages demo install clean

help:
	@echo "openunit make targets:"
	@echo "  make verify    determinism guard + vintages reproduce + demo (no deps)"
	@echo "  make test      full pytest suite"
	@echo "  make guard     determinism guard only"
	@echo "  make vintages  rewrite the data vintages under data/"
	@echo "  make demo      run the illustrative demo"
	@echo "  make install   pip install -e .[dev]"
	@echo "  make clean     remove caches and build artifacts"

# One command that proves the core claim, using the standard library only.
verify: guard
	$(PYTHON) make_vintages.py --verify
	$(PYTHON) test_vintages.py
	$(PYTHON) test_ppp.py
	$(PYTHON) test_cli.py
	$(PYTHON) test_anchor.py
	$(PYTHON) openunit.py

guard:
	$(PYTHON) test_determinism_guard.py

test:
	$(PYTHON) -m pytest -q

vintages:
	$(PYTHON) make_vintages.py

demo:
	$(PYTHON) openunit.py

install:
	$(PYTHON) -m pip install -e ".[dev]"

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info build dist
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
