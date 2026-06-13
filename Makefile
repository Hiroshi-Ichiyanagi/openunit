PYTHON ?= python3

.PHONY: help verify verify-independent test guard vintages demo install clean

help:
	@echo "openunit make targets:"
	@echo "  make verify              determinism guard + vintages reproduce + demo (no deps)"
	@echo "  make verify-independent  re-verify every vintage with the independent verifier"
	@echo "  make test                full pytest suite"
	@echo "  make guard               determinism guard only"
	@echo "  make vintages            rewrite the data vintages under data/"
	@echo "  make demo                run the illustrative demo"
	@echo "  make install             pip install -e .[dev]"
	@echo "  make clean               remove caches and build artifacts"

# One command that proves the core claim, using the standard library only.
verify: guard
	$(PYTHON) make_vintages.py --verify
	$(PYTHON) test_vintages.py
	$(PYTHON) test_ppp.py
	$(PYTHON) test_cli.py
	$(PYTHON) test_anchor.py
	$(PYTHON) test_independent.py
	$(PYTHON) test_properties.py
	$(MAKE) verify-independent
	$(PYTHON) openunit.py

# Second-implementation check: every shipped vintage must pass the verifier
# that never imports the engine (verify_independent.py).
verify-independent:
	@set -e; for d in data/*/; do \
		$(PYTHON) verify_independent.py "$$d/spec.json" "$$d/artifact.json"; \
	done

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
