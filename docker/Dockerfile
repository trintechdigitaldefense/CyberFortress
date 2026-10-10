FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 cfops \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin cfops

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Writable runtime dirs for non-root
RUN mkdir -p /app/logs /app/evidence /app/secrets /app/telemetry \
    && chown -R cfops:cfops /app

USER cfops

CMD ["python3", "-m", "agents.threat_hunting_agent"]
