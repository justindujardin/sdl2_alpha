# Blendy Build and Test Makefile

.PHONY: build install test test-release clean dev docs

# Development build (debug mode)
build:
	maturin develop

# Release build and install
install:
	maturin build --release
	pip install target/wheels/*.whl --force-reinstall

# Run all tests
test: build
	pytest tests/ -v

# Run tests with release build for performance testing  
test-release: install
	pytest tests/ -v -m "not slow"
	pytest tests/test_performance.py -v -s

# Clean build artifacts
clean:
	cargo clean
	rm -rf target/
	rm -rf *.egg-info/
	rm -rf build/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Development setup
dev:
	pip install maturin pytest pillow numpy
	maturin develop

# Build documentation (if needed later)
docs:
	@echo "Documentation build not yet implemented"

# Quick development cycle
quick: build test

# CI/CD pipeline simulation
ci: clean dev test-release

# Help
help:
	@echo "Available targets:"
	@echo "  build        - Development build (debug mode)"
	@echo "  install      - Release build and install" 
	@echo "  test         - Run all tests with debug build"
	@echo "  test-release - Run tests with release build"
	@echo "  clean        - Clean all build artifacts"
	@echo "  dev          - Set up development environment"
	@echo "  quick        - Quick development cycle (build + test)"
	@echo "  ci           - Simulate CI/CD pipeline"
	@echo "  help         - Show this help message"