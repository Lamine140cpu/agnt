FROM python:3.11-slim

# Dépendances système pour Playwright/Chromium
RUN apt-get update && apt-get install -y \
    wget curl gnupg \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    libx11-xcb1 libxcb-dri3-0 libxss1 libxtst6 \
    fonts-liberation xdg-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer Chromium via Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

EXPOSE 8080

CMD ["python", "server.py"]
