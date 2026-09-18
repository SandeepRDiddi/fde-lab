# Build context for this Dockerfile is infra/k8s/ (not this directory) so
# it can also COPY the chart in:
#   docker build -f infra/k8s/provisioner/Dockerfile -t fde-lab-k8s-provisioner:local infra/k8s
#
# Needs `helm` (renders/applies the chart) and `kubectl` (helm's own
# dependency for talking to the API server) baked in -- neither ships in
# python:3.11-slim, unlike the pip-installable dependencies every other
# service in this repo needs.
FROM python:3.11-slim

ARG HELM_VERSION=v3.14.4
ARG KUBECTL_VERSION=v1.29.3

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" | tar -xz -C /tmp && \
    mv /tmp/linux-amd64/helm /usr/local/bin/helm && \
    curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" && \
    chmod +x /usr/local/bin/kubectl && \
    rm -rf /var/lib/apt/lists/* /tmp/linux-amd64

WORKDIR /app

COPY provisioner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY provisioner/app ./app
COPY chart ./chart

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
