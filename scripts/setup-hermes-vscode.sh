#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama was not found. Install it from https://ollama.com and rerun this script." >&2
  exit 1
fi

ollama pull hermes3:latest

echo "Hermes model is ready."
echo "Next steps:"
echo "1. Install the Continue extension in VS Code."
echo "2. Reload the window."
echo "3. Open the Chat panel and select the Hermes Local model."
