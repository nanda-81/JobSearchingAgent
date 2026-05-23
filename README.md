# Personalized Job Search Automation Platform (PJSAP)

Personalized Job Search Automation Platform (PJSAP) is an intelligent, high-speed, privacy-first, and containerized system that crawls, aggregates, normalizes, matches, and ranks job postings from 100+ sources in real-time. 

---

## 1. System Architecture

PJSAP operates as a modular, containerized multi-service ecosystem. The following high-level diagram illustrates the data flow, storage partitioning, and system components:

```mermaid
graph TD
    Client[React Dashboard / Mobile Client] <--> |HTTPS / JWT Auth| Gateway[FastAPI REST API / Gateway]
    Gateway <--> |Sessions & JWT Validation| Cache[(Redis Cache)]
    Gateway <--> |Read / Write Schema| DB[(PostgreSQL Primary)]
    
    %% Async Job Processing
    CrawlerScheduler[Celery Scheduler] --> |Dispatch Crawl Tasks| Queue[RabbitMQ Broker]
    CrawlerWorkers[Celery Worker Cluster] <--> |Dequeue Tasks| Queue
    
    CrawlerWorkers --> |HTTP Requests / OAuth| Sources[Job Boards / Social Channels: LinkedIn, Indeed, X]
    CrawlerWorkers --> |Write Normalized Jobs| DB
    CrawlerWorkers --> |Index for Text Search| ES[Elasticsearch Node]
    
    %% Matching & Analytics
    MatchingEngine[Celery Matching Worker] <--> |Triggers on Crawled Jobs| DB
    MatchingEngine <--> |Text queries & Filters| ES
    MatchingEngine --> |Compute TF-IDF & Cosine Similarity| ML[Local Cosine Vector / scikit-learn]
    MatchingEngine --> |Write Ranked Matches| DB
    
    %% Notifications
    MatchingEngine --> |Publish Alerts| Queue
    NotificationService[Celery Notifier Worker] <--> |Dequeue Alert Tasks| Queue
    NotificationService --> |Encrypted Credentials| DB
    NotificationService --> |Push / API webhook| Webhooks[Social Notifications: Telegram, X, WhatsApp]
```

---

## 2. Technical Stack & Service Specifications

| Component | Technical Choice | Purpose & Configuration |
| :--- | :--- | :--- |
| **Gateway / Backend** | Python FastAPI (Async) | Serves REST endpoints, implements JWT verification, manages DB connection pools. |
| **Primary Database** | PostgreSQL 15 | Relational data persistence, schema enforcement, transactional integrity. |
| **Caching Layer** | Redis 7 | User session caching, rate-limiting, and short-term job query buffering. |
| **Search Engine** | Elasticsearch 7.17 | High-speed, fuzzy, full-text job search and initial filtering. |
| **Message Queue** | RabbitMQ 3 | Reliable, concurrent task dispatching for workers. |
| **Task Runner** | Celery 5.3 | Scheduled crawlers and decoupled matching pipelines. |
| **UI Dashboard** | React 18, TypeScript, Vite | Premium modern SPA featuring real-time updates and interactive profiling. |

---

## 3. Database Schema

The database consists of 6 core tables orchestrated in PostgreSQL with standard referential constraints, cascades, indexes, and range checks.

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar full_name
        boolean is_active
        boolean is_superuser
        timestamp created_at
        timestamp updated_at
    }
    USER_PROFILES {
        uuid user_id PK, FK
        jsonb target_titles
        jsonb target_locations
        integer salary_min
        varchar experience_level
        jsonb job_types
        jsonb keywords
        jsonb excluded_keywords
        varchar resume_url
        boolean consent_given
        timestamp created_at
        timestamp updated_at
    }
    JOBS {
        uuid id PK
        varchar source
        varchar original_id
        varchar title
        varchar company
        varchar location
        boolean is_remote
        text description
        integer salary_min
        integer salary_max
        varchar salary_currency
        varchar url UK
        timestamp posted_at
        timestamp processed_at
        jsonb raw_data
        varchar hash_key UK
        timestamp created_at
    }
    JOB_MATCHES {
        uuid user_id PK, FK
        uuid job_id PK, FK
        double match_score
        jsonb matching_details
        varchar status
        timestamp created_at
        timestamp updated_at
    }
    SOCIAL_CREDENTIALS {
        uuid user_id PK, FK
        text twitter_token
        varchar telegram_chat_id
        varchar whatsapp_phone
        timestamp updated_at
    }
    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        varchar action
        varchar ip_address
        varchar user_agent
        jsonb payload
        timestamp created_at
    }

    USERS ||--|| USER_PROFILES : "has"
    USERS ||--o{ JOB_MATCHES : "gets"
    JOBS ||--o{ JOB_MATCHES : "linked_to"
    USERS ||--|| SOCIAL_CREDENTIALS : "authenticates"
    USERS ||--o{ AUDIT_LOGS : "triggers"
```

---

## 4. Resilience and Error Handling Design

To achieve production-grade stability, all crawler operations and API calls integrate the following robustness frameworks:

1. **Exponential Backoff with Jitter:**
   - Failed HTTP requests or crawler executions retry after `initial_delay * (backoff_factor ^ attempt) + random_jitter`.
   - Prevents cascading network saturation or getting blacklisted by remote targets due to synchronized retries.
2. **Circuit Breaker Pattern:**
   - Any crawler tracking consecutive failures (e.g. 5 failures to reach LinkedIn) trips its internal circuit.
   - Immediate subsequent crawl tasks for LinkedIn fail-fast with cached error states for 10 minutes to save queue execution cycles.
3. **Graceful Degradation:**
   - If Elasticsearch fails, searches gracefully fall back to executing `ILIKE` database queries in PostgreSQL, and alerts are queued as soon as connections resume.
   - If RabbitMQ goes offline, API requests log incoming events directly to the database for reconciliation upon recovery.

---

## 5. Security & Privacy-First Framework

GDPR/CCPA principles are baked into the core architectural design:
- **AES-256 Symmetric Encryption:** All social API credentials, Telegram IDs, and phone numbers are encrypted at-rest. Decryption happens dynamically on the runtime worker memory boundary and is never persisted in plaintext.
- **Strict Auditing:** The `audit_logs` table logs all security, credential edits, and GDPR actions.
- **Data Portability & Deletion:** Standard endpoints `/api/v1/gdpr/export` and `/api/v1/gdpr/delete` allow user profiles to be immediately backed up as normalized JSON, or wiped from the database recursively using cascade constraints.
