.PHONY: run week api test-sample

# Default Python interpreter
PYTHON = python3

# Main execution target
run:
	$(PYTHON) main.py

# Weekly execution target
week:
	$(PYTHON) main.py --mode=weekly

# API execution target
api:
	$(PYTHON) main.py --mode=api

# Test sample execution target
test-sample:
	$(PYTHON) main.py --csv-dir samples/data --once --no-telegram

# Help target
help:
	@echo "Available targets:"
	@echo "  run         - Run main application"
	@echo "  week        - Run weekly analysis"
	@echo "  api         - Run API mode"
	@echo "  test-sample - Run test sample"
	@echo "  help        - Show this help message"
