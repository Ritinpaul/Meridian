# Meridian Implementation Plan

Implementation Status (2026-04-20):
- Phase 1: Completed
- Phase 2: Completed

Project: Meridian - Real-Time Geospatial Operations Intelligence
Stack: Next.js 14, TypeScript, FastAPI, PostgreSQL (PostGIS), Redis Pub/Sub, WebSocket, LangChain
Date: 2026-04-20

## 1) Goal
Build a real-time geospatial command center that tracks moving entities at low latency, detects route anomalies with high precision, and provides natural-language operational querying for non-technical analysts.

## 2) Success Metrics
- Real-time scale: >= 200 entities concurrently tracked on live map
- Stream latency: < 500 ms median update latency from ingest to dashboard render
- Anomaly quality: >= 92% precision on route deviation detection benchmark
- NL analytics productivity: >= 65% reduction in report generation time
- Query reliability: >= 95% success rate for NL to SQL translation on test prompts
- System reliability: >= 99% message delivery in stress scenarios

## 3) MVP Scope (Fast and Practical)
In scope:
1. WebSocket-based real-time entity updates
2. Redis Pub/Sub event bus for low-latency fanout
3. PostGIS-backed entity state and geospatial query layer
4. ML anomaly detection for route deviation alerts
5. LangChain natural-language query to geospatial SQL
6. Next.js operations dashboard with map and alert stream
7. Benchmark suite for latency and analyst productivity gains

Out of scope for MVP:
- Mobile applications
- Multi-region active-active deployment
- Historical BI warehouse integration

## 4) High-Level Architecture
1. Ingestion Gateway (FastAPI + WebSocket)
- Receives position updates and validates telemetry payloads.
- Publishes normalized events to Redis Pub/Sub channels.

2. Stream and State Layer
- Redis Pub/Sub handles low-latency event distribution to services.
- State writer persists latest and historical positions in PostGIS tables.

3. Anomaly Detection Service
- Evaluates route adherence and speed or heading deviations.
- Emits anomaly events with precision-scored reasons.

4. NL Query Service (LangChain)
- Translates plain-English operational questions to SQL and geospatial queries.
- Returns structured answers and analyst-friendly summaries.

5. Application Layer
- FastAPI APIs plus WebSocket stream endpoints.
- Next.js dashboard for map visualization, alerts, and reports.

## 5) Proposed Folder Structure
meridian/
- backend/
  - app/
    - api/
    - stream/
    - anomaly/
    - geospatial/
    - nl_query/
    - db/
- frontend/
  - app/
  - components/
  - map/
- tests/
- scripts/
- docker-compose.yml
- README.md

## 6) Data Model (PostgreSQL and PostGIS)
Tables:
1. entities
- entity_id (pk)
- external_id
- type
- status
- last_seen_at

2. position_events
- event_id (pk)
- entity_id (fk)
- event_time
- latitude
- longitude
- speed
- heading
- geom (geography point)

3. route_definitions
- route_id (pk)
- route_name
- corridor_geom (geometry)
- max_deviation_meters

4. anomaly_events
- anomaly_id (pk)
- entity_id (fk)
- route_id (fk)
- anomaly_type
- anomaly_score
- reason
- detected_at

5. nl_query_audit
- query_id (pk)
- user_id
- question
- sql_generated
- execution_ms
- success
- created_at

6. report_runs
- report_id (pk)
- report_type
- input_window
- generated_at
- generation_ms

## 7) API Contract (FastAPI)
Endpoints:
1. WS /stream/positions
- input: live position payload stream
- output: ack plus broadcast to subscribers

2. POST /entities/positions/batch
- input: array of telemetry records
- output: accepted count, rejected count

3. GET /entities/live
- output: latest known position per active entity

4. POST /anomalies/detect
- input: time window and optional entity scope
- output: anomaly list with precision-oriented metadata

5. POST /query/natural-language
- input: plain-English operational question
- output: SQL, result summary, rows

6. GET /reports/operations-summary
- output: generated operational intelligence report

## 8) Phase-Wise Implementation Plan (12 Days)

### Phase 1: Foundation and Real-Time Ingest (Days 1-2)
Step 1 (Day 1): Platform bootstrap
- Initialize backend plus frontend, PostGIS schema, Redis, and auth baseline.
- Deliverable: local stack with health checks and map shell.

Step 2 (Day 2): WebSocket ingest and fanout
- Implement telemetry validation and Redis Pub/Sub broadcast.
- Deliverable: live position events visible in console subscribers.

Phase 1 exit criteria:
- Real-time ingest path is stable.
- Core services start and communicate correctly.

### Phase 2: Geospatial State and Mapping (Days 3-5)
Step 1 (Day 3): State persistence layer
- Persist position events and latest entity state in PostGIS.
- Deliverable: queryable latest-position service.

Step 2 (Day 4): Map dashboard rendering
- Render 200+ entities with incremental updates.
- Deliverable: live map with marker clustering and status indicators.

Step 3 (Day 5): Performance pass
- Optimize write/read path for sub-500ms streaming latency.
- Deliverable: latency benchmark report for stream path.

Phase 2 exit criteria:
- Dashboard tracks target entity volume.
- Stream latency target is met in benchmark scenario.

### Phase 3: Anomaly Intelligence (Days 6-8)
Step 1 (Day 6): Route model and baseline detectors
- Add route corridor checks and heading or speed anomaly rules.
- Deliverable: anomaly pipeline with explainable reason codes.

Step 2 (Day 7): Precision tuning
- Calibrate thresholds on labeled route-deviation dataset.
- Deliverable: >= 92% precision in offline evaluation.

Step 3 (Day 8): Alert feed integration
- Publish anomaly events to dashboard alert timeline.
- Deliverable: real-time alert stream with context detail.

Phase 3 exit criteria:
- Detection precision target is achieved.
- Alerts are visible and actionable in UI.

### Phase 4: NL Query and Reporting (Days 9-10)
Step 1 (Day 9): LangChain NL to SQL service
- Convert analyst prompts into geospatial SQL with safeguards.
- Deliverable: query endpoint with audit logging.

Step 2 (Day 10): Analyst reporting workflow
- Build report generation endpoint and dashboard report cards.
- Deliverable: benchmarked report workflow with time-savings evidence.

Phase 4 exit criteria:
- NL query flow is reliable and auditable.
- Reporting workflow demonstrates target productivity gain.

### Phase 5: Validation and Portfolio Packaging (Days 11-12)
Step 1 (Day 11): End-to-end validation
- Run load, latency, anomaly precision, and NL query success tests.
- Deliverable: consolidated benchmark and quality report.

Step 2 (Day 12): Production polish
- Finalize README, architecture diagram, demo scripts, and dashboard snapshots.
- Deliverable: recruiter-ready project package.

Phase 5 exit criteria:
- Performance and quality evidence complete.
- Project is reproducible and demo-ready.

## 9) Testing and Verification
Automated tests:
- Unit tests for geospatial transforms, anomaly scoring, and NL query parsing
- Integration tests for ingest to redis to postgis flow
- End-to-end tests for dashboard streams and report generation

Quality gates:
- Test pass rate 100%
- Latency benchmark under target threshold
- Precision and productivity metrics validated on benchmark scenarios

## 10) Deployment Plan (MVP)
- Docker Compose deployment for local and VM setup
- Services: frontend, backend, postgres-postgis, redis, worker
- Optional Nginx reverse proxy for TLS termination

## 11) Resume Proof Checklist
- Dashboard screenshot tracking 200+ entities in real time
- Latency benchmark proving sub-500ms stream performance
- Anomaly precision report at or above 92%
- NL query and report benchmark showing around 65% time reduction
