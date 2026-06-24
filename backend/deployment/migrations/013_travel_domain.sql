-- Migration 013: Travel domain tables
-- Covers: TravelRequest, TravelItinerarySegment
-- Spec: docs/canon/domain-model.md, docs/canon/data-architecture.md,
--       docs/canon/workflow-catalog.md §travel_request (G48)

BEGIN;

-- ---------------------------------------------------------------------------
-- travel_requests
-- Employee travel requests routed through the centralized workflow engine.
-- State machine: Draft -> Submitted -> Approved/Rejected
--                Approved -> Booked -> Completed
--                Draft/Submitted/Approved/Booked -> Cancelled
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS travel_requests (
    tenant_id               VARCHAR(80)     NOT NULL,
    travel_request_id       UUID            NOT NULL DEFAULT uuid_generate_v4(),
    employee_id             UUID            NOT NULL,
    manager_employee_id     UUID            NULL,
    purpose                 VARCHAR(240)    NOT NULL,
    destination             VARCHAR(240)    NOT NULL,
    start_date              DATE            NOT NULL,
    end_date                DATE            NOT NULL CHECK (end_date >= start_date),
    status                  VARCHAR(20)     NOT NULL DEFAULT 'Draft'
                                CHECK (status IN (
                                    'Draft','Submitted','Approved','Rejected',
                                    'Booked','Completed','Cancelled'
                                )),
    workflow_id             UUID            NULL,
    estimated_cost          NUMERIC(12,2)   NULL CHECK (estimated_cost >= 0),
    currency                CHAR(3)         NOT NULL DEFAULT 'PKR',
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_travel_requests PRIMARY KEY (travel_request_id),
    CONSTRAINT fk_travel_requests_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    CONSTRAINT fk_travel_requests_manager
        FOREIGN KEY (manager_employee_id) REFERENCES employees (employee_id)
);

CREATE INDEX IF NOT EXISTS idx_travel_requests_tenant_id
    ON travel_requests (tenant_id);
CREATE INDEX IF NOT EXISTS idx_travel_requests_employee_id
    ON travel_requests (employee_id);
CREATE INDEX IF NOT EXISTS idx_travel_requests_manager_id
    ON travel_requests (manager_employee_id);
CREATE INDEX IF NOT EXISTS idx_travel_requests_tenant_status
    ON travel_requests (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_travel_requests_start_date
    ON travel_requests (tenant_id, start_date);

-- ---------------------------------------------------------------------------
-- travel_itinerary_segments
-- Individual travel legs (flight, hotel, car, train) attached to a request.
-- Created/updated after the request is Approved.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS travel_itinerary_segments (
    tenant_id           VARCHAR(80)     NOT NULL,
    segment_id          UUID            NOT NULL DEFAULT uuid_generate_v4(),
    travel_request_id   UUID            NOT NULL,
    segment_type        VARCHAR(30)     NOT NULL
                            CHECK (segment_type IN ('Flight','Hotel','Car','Train','Other')),
    departure_city      VARCHAR(120)    NOT NULL,
    arrival_city        VARCHAR(120)    NOT NULL,
    departure_at        TIMESTAMPTZ     NOT NULL,
    arrival_at          TIMESTAMPTZ     NOT NULL CHECK (arrival_at >= departure_at),
    provider_name       VARCHAR(120)    NULL,
    booking_reference   VARCHAR(80)     NULL,
    cost                NUMERIC(12,2)   NULL CHECK (cost >= 0),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_travel_itinerary_segments PRIMARY KEY (segment_id),
    CONSTRAINT fk_travel_segments_request
        FOREIGN KEY (travel_request_id) REFERENCES travel_requests (travel_request_id)
            ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_travel_segments_tenant_id
    ON travel_itinerary_segments (tenant_id);
CREATE INDEX IF NOT EXISTS idx_travel_segments_request_id
    ON travel_itinerary_segments (travel_request_id);
CREATE INDEX IF NOT EXISTS idx_travel_segments_departure_at
    ON travel_itinerary_segments (travel_request_id, departure_at);

COMMIT;
