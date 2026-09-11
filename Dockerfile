# ---------- Stage 1: Install Consumet ----------
FROM node:20-slim AS consumet-builder

WORKDIR /consumet
COPY package.json ./
RUN npm install --omit=dev

# ---------- Stage 2: Final Image ----------
FROM python:3.11-slim

# Install Node.js, curl, git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Consumet from builder stage
COPY --from=consumet-builder /consumet /app/consumet

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
EXPOSE 8080

# Run both services via start script
CMD ["./start.sh"]
