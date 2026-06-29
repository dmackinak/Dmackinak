#!/bin/bash
set -e

echo "=== YouTube Shorts Auto-Cutter Setup ==="

# ── Backend deps ──────────────────────────────────────────────────────────────
echo ""
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

# ── Check ffmpeg ──────────────────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
  echo ""
  echo "⚠  ffmpeg not found in PATH — imageio_ffmpeg will be used instead (already installed)."
else
  echo "✓  ffmpeg $(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')"
fi

# ── Frontend deps ─────────────────────────────────────────────────────────────
echo ""
echo "Installing Node.js dependencies..."
cd frontend
npm install
echo "Building frontend..."
npm run build
cd ..

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start the server:"
echo "  cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Then open: http://localhost:8000"
