#!/usr/bin/env bash
# exit on error
set -o errexit

echo "==> Upgrading pip and build tools..."
python -m pip install --upgrade pip

echo "==> Installing production dependencies..."
pip install -r requirements.txt

echo "==> Build complete!"
