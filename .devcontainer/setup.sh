#!/bin/bash
# .devcontainer/setup.sh
# Additional setup script

set -e

echo "🔧 Running additional setup..."

# Create Python virtual environment (optional)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "✅ Virtual environment created"
fi

# Install development tools
echo "🛠️ Installing development tools..."
pip install --upgrade \
    black \
    flake8 \
    isort \
    pytest \
    pytest-cov \
    pytest-xdist \
    mypy \
    pre-commit \
    pylint \
    bandit \
    safety

# Setup pre-commit hooks
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo "🔧 Setting up pre-commit hooks..."
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length=100]
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
EOF
    pre-commit install
fi

# Create test directory
mkdir -p tests
touch tests/__init__.py

echo "✅ Setup complete!"
