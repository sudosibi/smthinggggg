#!/bin/bash
set -e

echo "🍟♤ ｐ𝓞т𝐀tᵒ 🐟🎁 Anime API starting..."

# Start Consumet in the background
echo "[+] Starting Consumet on port 3000..."
node /app/consumet/node_modules/@consumet/api.consumet.org/dist/index.js &
CONSUMET_PID=$!

# Wait for Consumet to be ready
echo "[+] Waiting for Consumet..."
for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:3000 > /dev/null 2>&1; then
    echo "[+] Consumet is live!"
    break
  fi
  sleep 1
done

# Start Flask API on Railway's $PORT
echo "[+] Starting Flask API on port $PORT..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
