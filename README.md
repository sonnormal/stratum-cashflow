# 💰 Stratum Cashflow Service (`services/cashflow`)

> **Domain:** Financial Core & Cashflow Ledger  
> **Runtime:** Python 3.12+ / FastAPI / PostgreSQL 16  
> **Status:** `ACTIVE` (TDD Phase 1 - `Red`)

---

## 📌 Responsibilities
* Persists authoritative bank transaction movements into PostgreSQL (`account_movements`).
* Guarantees atomic idempotency via composite unique key on `(bank_code, raw_source_ref)`.
* Provides REST API endpoints (`/api/v1/movements`) consuming `TransactionDetectedEvent` (v1).
* Exposes `/healthz` liveness and `/readyz` readiness probes.

---

## 🧪 Testing & Verification
```bash
# Activate virtual environment
source .venv/bin/activate

# Run Tier 1 (Unit) and Tier 2 (Integration with Testcontainers)
PYTHONPATH=src pytest
```
