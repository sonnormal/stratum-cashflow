# 🧪 Stratum Repository Specification & Test Scenarios: services/cashflow

> **Document Type:** Repo-Specific Technical Specification & Executable Acceptance Tests (`STEP-04` Red Phase)  
> **Target Checkpoint:** `GATE-02` (Contract & Test Scenario Gate)  
> **Location:** `services/cashflow/changes/CR-26j001-bank-cashflow-ingestion/scenario.md`  
> **Scope:** Strictly isolated to `services/cashflow` for **Technical Design**, **Tier 1 (Unit Tests)**, and **Tier 2 (Integration Tests)**.

---

## 📌 1. Target Repository Metadata

| Field | Detail |
| :--- | :--- |
| **Change ID** | `CR-26j001` |
| **Target Repository** | [`services/cashflow`](file:///Users/son/Projects/Stratum/services/cashflow) |
| **Feature Fulfillments** | [FEAT-001: Bank Transaction Ingestion & Cashflow Alerting](file:///Users/son/Projects/Stratum/stratum-meta/features/vib-transaction-alert.md) |
| **Associated Flow** | [FLOW-001: Inbound Email Transaction Ingestion & Alerting](file:///Users/son/Projects/Stratum/stratum-meta/flows/email-transaction-ingestion.md) |
| **Bound Contracts** | [TransactionDetectedEvent (v1)](file:///Users/son/Projects/Stratum/stratum-meta/contracts/events/transaction_detected.v1.json) |
| **Author** | AI Verification Architect |
| **Status** | `PENDING_GATE_02_APPROVAL` |
| **Master CR Record** | [CR-26j001 Evaluation Report](file:///Users/son/Projects/Stratum/stratum-meta/changes/CR-26j001-bank-cashflow-ingestion/evaluation.md) |

---

## 📐 2. Technical Scope & Implementation Invariants

### 2.1 Modules & Components to Create
* **`src/cashflow/domain/models.py`:** Pure domain value objects (`TransactionType`, `Currency`, `AccountMovement`). Enforces decimal precision (zero IEEE 754 float rounding errors).
* **`src/cashflow/domain/service.py`:** Core domain service (`CashflowService`). Orchestrates movement recording, checks duplicate status, and formats notification payload.
* **`src/cashflow/db/models.py`:** SQLAlchemy ORM model for `account_movements` table.
* **`src/cashflow/db/repository.py`:** Persistence repository with atomic idempotency using `INSERT ... ON CONFLICT (bank_code, raw_source_ref) DO NOTHING`.
* **`src/cashflow/api/routes.py`:** FastAPI endpoint `POST /api/v1/movements` conforming to `TransactionDetectedEvent` (v1).
* **`src/cashflow/api/main.py`:** FastAPI application entrypoint with health probes (`/healthz`).

### 2.2 Data Persistence & Schema Invariants
* **Table:** `account_movements`
  * `id`: UUID (Primary Key)
  * `event_id`: UUID (NOT NULL)
  * `occurred_at`: TIMESTAMPTZ (NOT NULL)
  * `bank_code`: VARCHAR(10) (NOT NULL)
  * `account_number_mask`: VARCHAR(20) (NULLABLE)
  * `transaction_type`: VARCHAR(10) (NOT NULL, check: `DEBIT` or `CREDIT`)
  * `amount`: NUMERIC(15, 2) (NOT NULL, check: `amount > 0`)
  * `currency`: VARCHAR(3) (NOT NULL, default: `VND`)
  * `description`: TEXT (NULLABLE)
  * `counterparty`: VARCHAR(255) (NULLABLE)
  * `category`: VARCHAR(100) (NULLABLE)
  * `raw_source_ref`: VARCHAR(255) (NOT NULL)
  * `created_at`: TIMESTAMPTZ (DEFAULT NOW())
* **Composite Unique Constraint:** `UNIQUE (bank_code, raw_source_ref)`
  * Guarantees zero duplicate writes even under concurrent re-delivery.

### 2.3 Dependencies & Configuration
* **Dependencies:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, psycopg 3, pytest, testcontainers-python.
* **Configuration:** `DATABASE_URL` (PostgreSQL connection string).

---

## 🔬 3. Tier 1: Unit Test Scenarios (In-Memory Isolation)

*Zero network, zero disk I/O. Execution budget < 10ms.*

### Scenario 1.1: Valid Movement Entity Construction
* **Given:** A valid dictionary matching `TransactionDetectedEvent` (v1) with amount `75000` VND.
* **When:** `AccountMovement.from_contract(payload)` is invoked.
* **Then:** The domain entity is constructed with exact `Decimal("75000.00")`, normalized enum `TransactionType.DEBIT`, and valid fields.

### Scenario 1.2: Negative or Zero Amount Rejection
* **Given:** A payload with `amount = 0` or `amount = -50000`.
* **When:** `AccountMovement.from_contract(payload)` is invoked.
* **Then:** A domain `ValueError` is raised with message specifying that movement amount must be strictly positive.

### Scenario 1.3: Idempotent Duplicate Handling in Domain Service
* **Given:** A mocked repository that returns `is_new=False` when saving a duplicate movement.
* **When:** `CashflowService.record_movement(movement)` is called.
* **Then:** The service returns `MovementResult(status=Status.DUPLICATE_IGNORED)` and does **not** trigger a notification event.

### Scenario 1.4: New Movement Success Handling in Domain Service
* **Given:** A mocked repository that returns `is_new=True`.
* **When:** `CashflowService.record_movement(movement)` is called.
* **Then:** The service returns `MovementResult(status=Status.RECORDED, movement=...)`.

---

## 🔌 4. Tier 2: Integration Test Scenarios (Testcontainers PostgreSQL)

*Executes against real PostgreSQL 16 container managed by `testcontainers-python` in OrbStack.*

### Scenario 2.1: Schema Table Creation & Atomic Insert
* **Given:** An isolated PostgreSQL 16 container booted by Testcontainers with schema initialized.
* **When:** A new movement is persisted via `PostgresMovementRepository`.
* **Then:** The row is saved with 100% precision in `account_movements`, and `is_new=True` is returned.

### Scenario 2.2: Atomic Idempotency via Composite Unique Key
* **Given:** An existing transaction record in PostgreSQL with `bank_code='VIB'` and `raw_source_ref='RFC822-MSG-20261006-VIB-001'`.
* **When:** A second insert attempt is executed with the exact same `(bank_code, raw_source_ref)`.
* **Then:** The database executes `ON CONFLICT DO NOTHING`, zero duplicate rows are added, and the repository returns `is_new=False` without throwing an unhandled SQL exception.

### Scenario 2.3: FastAPI REST Endpoint `/api/v1/movements`
* **Given:** The FastAPI application connected to the Testcontainers PostgreSQL instance.
* **When:** Client sends `POST /api/v1/movements` with `valid_movement_event.json`.
* **Then:** Response status is `201 Created` with JSON `{ "status": "RECORDED", "movement_id": "..." }`.
* **When:** Client sends the identical payload again.
* **Then:** Response status is `200 OK` with JSON `{ "status": "DUPLICATE_IGNORED" }`.

---

## 📂 5. Test Fixtures Inventory (`fixtures/`)

| Fixture File | Type | Used In Scenario | Description |
| :--- | :--- | :--- | :--- |
| `fixtures/valid_movement_event.json` | JSON | Scenario 1.1, 2.1, 2.3 | Valid VIB debit transaction with counterparty and category |

---

## ⚖️ 6. GATE-02 Verification Checklist

- [ ] Technical scope respects repository boundary (Domain persistence only, no IMAP or Viber tokens).
- [ ] Tier 1 tests run in-memory (< 10ms) with zero I/O.
- [ ] Tier 2 tests execute against ephemeral Testcontainers PostgreSQL on OrbStack.
- [ ] Test fixtures contain zero real credentials or PII.
- [ ] Automated tests fail cleanly (`Red` state) awaiting code synthesis (`STEP-05`).
