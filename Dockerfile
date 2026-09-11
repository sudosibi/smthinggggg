# ---------- Stage 1: Pull official Consumet image ----------
FROM riimuru/consumet-api:latest AS consumet

# ---------- Stage 2: Final Image ----------
FROM python:3.11-slim

# Install curl + Node.js (for Consumet binary)
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Consumet app from official image
COPY --from=consumet /app /app/consumet

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app.py .
COPY start.sh .
RUN chmod +x start.sh

# Railway provides $PORT at runtime
ENV PORT=8080
ENV NODE_ENV=PROD
EXPOSE 8080

# Run both services via start script
CMD ["./start.sh"]
