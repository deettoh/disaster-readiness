# Hyperlocal Disaster Readiness (Malaysia)

## Directory map

| Directory | What it is for | Who owns it |
| --- | --- | --- |
| `apps/frontend/` | React + Tailwind + MapLibre web app (mobile-first browser UX). Frontend source lives in `apps/frontend/src/`. | Member E (Frontend + UX) |
| `apps/api/` | FastAPI service, API contracts, validation, and orchestration endpoints. Python package source lives in `apps/api/src/app/`. | Member A (Backend Lead) |
| `apps/worker/` | Background job worker (Redis + RQ) for async pipelines. Python package source lives in `apps/worker/src/worker/`. | Member A + Member D |
| `db/migrations/` | SQL migrations for Postgres/PostGIS schema changes. | Member B (Data + Geospatial) |
| `db/seeds/` | Seed scripts/data for local dev and demo baseline records. | Member B |
| `db/functions/` | SQL functions/views for readiness, hazard aggregation, and geospatial helpers. | Member B (with C support for routing queries) |
| `db/policies/` | RLS and data access policy SQL definitions. | Member B + Member A |
| `routing/sql/` | pgRouting SQL, snapping, route queries, penalty update logic, accessibility metrics. | Member C (Routing Lead) |
| `routing/data/` | Routing input assets (OSM extracts, prepared graph artifacts/metadata). | Member C + Member B |
| `ai/classification/` | Hazard image classification inference/training assets and model metadata. Python source lives in `ai/classification/src/hazard_classification/`. | Member D (AI + Privacy) |
| `ai/redaction/` | Face + plate detection and redaction pipeline code/assets. Python source lives in `ai/redaction/src/privacy_redaction/`. | Member D |
| `ai/imputation/` | Risk/vulnerability imputation model code, features, and artifacts. Python source lives in `ai/imputation/src/risk_imputation/`. | Member D + Member B |
| `shared/schemas/` | Shared API/data schemas used across frontend/backend/worker. | Member A + Member E |
| `shared/types/` | Shared constants/types/contracts for cross-module consistency. | Member A + Member E |
| `tests/api/` | API-level tests for endpoints, validation, and response contracts. | Member A |
| `tests/ai/` | Classification/redaction/imputation tests and quality checks. | Member D |
| `tests/routing/` | Routing query, penalty update, and accessibility metric tests. | Member C |
| `tests/integration/` | Cross-service integration tests (upload -> AI -> reroute -> readiness -> alerts). | Members A/B/C/D |
| `tests/e2e/` | End-to-end user flow tests from frontend through backend services. | Member E + Member A |
| `infra/docker/` | Dockerfiles and local container setup for API/worker/frontend. | Member A |
| `infra/deploy/` | Deployment configs/runbooks for Render/Cloud Run + Vercel/Netlify + Supabase. | Member A + Member E |
| `docs/architecture/` | Architecture diagrams and technical system design notes. | All members |
| `docs/api/` | API documentation, payload examples, and integration notes. | Member A |
| `docs/decisions/` | Decision records (scope, tradeoffs, implementation decisions). | All members (maintained by current implementer) |
| `docs/report/` | Hackathon report evidence, rubric mapping, and submission assets. | All members |
| `data/external/` | Raw external datasets (GIS, flood, rainfall, boundaries). | Member B |
| `data/processed/` | Processed/derived datasets ready for app and models. | Member B + Member D |
| `data/samples/` | Small sample files/images for local testing and demos. | Members C/D/E |
| `scripts/` | Automation scripts for setup, checks, and repeatable project tasks. | All members |
| `config/` | Non-secret config templates (for example `.env.example` and runtime config stubs). | Member A |

## Notes

- Empty scaffold directories include `.gitkeep` so they are tracked in Git.
- Poetry is initialized at repository root (`pyproject.toml`, `poetry.lock`, `.venv`).
