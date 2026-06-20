.PHONY: help run test selftest snapshot clean install

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

run:  ## Launch E-Console (needs a real terminal)
	python3 -m econsole

test:  ## Run the test suite (stdlib unittest, no deps)
	python3 -m unittest discover -t . -s tests -p 'test_*.py'

selftest:  ## Construct the shell headlessly and print a summary
	python3 -m econsole --self-test

snapshot:  ## Render a text snapshot of the default layout
	python3 tools/snapshot.py default --size 100x28

install:  ## Install the econsole launcher into the current environment
	python3 -m pip install -e .

clean:  ## Remove caches and build artifacts
	rm -rf build dist *.egg-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
