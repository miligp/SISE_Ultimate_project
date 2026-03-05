FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# ffmpeg requis pour openai-whisper et soundfile
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Installation des dépendances backend
COPY requirements-backend.txt .
RUN uv pip install --system --no-cache -r requirements-backend.txt

# Copie du code source
COPY src/ ./src/
COPY .env .env

EXPOSE 8001

CMD ["uv", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8001"]
