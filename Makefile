.PHONY: help install install-dev test test-unit test-integration lint format type-check clean run run-debug

# Default target
help:
	@echo "D-Bus MCP Server - Development Tasks"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-integration Run integration tests"
	@echo "  make lint          Run linting checks"
	@echo "  make format        Format code with black"
	@echo "  make type-check    Run mypy type checking"
	@echo ""
	@echo "Running:"
	@echo "  make run           Run the MCP server"
	@echo "  make run-debug     Run with debug logging"
	@echo ""
	@echo "Deployment:"
	@echo "  make install-systemd  Install systemd service files"
	@echo "  make build         Build distribution packages"
	@echo "  make clean         Clean build artifacts"

# Setup targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing targets
test:
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-security:
	pytest tests/unit/test_security.py -v

# Code quality targets
lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/

# Running targets
run:
	python -m dbus_mcp.server

run-debug:
	python -m dbus_mcp.server --log-level debug

run-workstation:
	python -m dbus_mcp.server --config config/workstation.yaml

run-server:
	python -m dbus_mcp.server --config config/server.yaml

# SystemD targets
install-systemd:
	./scripts/install-systemd.sh --user

install-systemd-system:
	sudo ./scripts/install-systemd.sh --system

# Build targets
build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development utilities
dbus-monitor:
	dbus-monitor --session

dbus-monitor-system:
	dbus-monitor --system

list-services:
	busctl --user list | grep -E "(org\.|com\.)" | sort

check-deps:
	pip list | grep -E "(mcp|pydbus|systemd)"