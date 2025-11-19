DIRS = src/ tests/ scripts/ examples/

gen:
	python scripts/compile_protos.py

lint:
	@echo "Running isort..."
	isort $(DIRS)
	
	@echo "Running black..."
	black $(DIRS)
	
	@echo "Running ruff (with fixes)..."
	ruff check --fix $(DIRS)
	
	@echo "✓ Linting complete!"

.PHONY: gen lint
