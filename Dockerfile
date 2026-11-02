FROM node:24-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS frontend
WORKDIR /source
COPY package.json package-lock.json tsconfig.json ./
COPY apps ./apps
COPY packages ./packages
COPY datasets ./datasets
RUN npm ci && npm run build

FROM python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd
WORKDIR /app
COPY requirements-lock.txt pyproject.toml README.md LICENSE ./
COPY packages ./packages
COPY services ./services
RUN pip install --no-cache-dir -r requirements-lock.txt && pip install --no-cache-dir . --no-deps \
    && useradd --create-home --uid 10001 nrs && mkdir /data && chown nrs:nrs /data
COPY --from=frontend /source/apps/research-console/dist ./static
COPY scripts/container_entrypoint.py ./container_entrypoint.py
ENV NX_STATIC_DIR=/app/static NX_DATABASE_URL=sqlite:////data/research.sqlite
USER nrs
EXPOSE 8876
CMD ["python", "container_entrypoint.py"]
