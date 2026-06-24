# Engagement Service

Employee engagement surveys, pulse campaigns, response capture, and aggregated sentiment analytics.

## Scope
- Manages survey lifecycle: creation, publishing, response capture, and aggregation.
- Supports pulse campaigns and periodic engagement surveys.
- Reuses `employee-service` read models for employee, manager, and department references.
- Publishes aggregated results for people analytics and executive sentiment dashboards.
- Does not duplicate workforce master data.

## HTTP surface (`/api/v1`)
- `POST /api/v1/engagement/surveys`
- `POST /api/v1/engagement/surveys/{survey_id}/publish`
- `POST /api/v1/engagement/surveys/{survey_id}/close`
- `GET /api/v1/engagement/surveys?status=`
- `GET /api/v1/engagement/surveys/{survey_id}`
- `POST /api/v1/engagement/responses`
- `GET /api/v1/engagement/surveys/{survey_id}/responses`
- `GET /api/v1/engagement/surveys/{survey_id}/aggregates`

## Authorization capabilities
- `CAP-ENG-001`: engagement surveys and analytics
  - Admin: full CRUD + publish + close + view all results
  - Manager: view aggregated results for own department; cannot see individual responses
  - Employee: submit own responses only; cannot view others' responses
  - PayrollAdmin / Recruiter: denied

## Owned entities
- `Survey`
- `SurveyQuestion`
- `SurveyResponse`
- `AggregatedSurveyResult`

## Supported workflows
- `engagement_feedback_collection`

## Events published
- `EngagementSurveyCreated`
- `EngagementSurveyPublished`
- `EngagementSurveyClosed`
- `EngagementSurveyResponseSubmitted`
- `EngagementSurveyResultsAggregated`

## Events subscribed
- `EmployeeCreated` / `EmployeeUpdated` / `EmployeeStatusChanged`

## Read models produced
- `engagement_survey_view` — survey status, response rates, aggregated sentiment
- Enriches people analytics and executive dashboards

## Dependencies
- `employee-service` — employee existence, department context, target-population scoping
- `notification-service` — pulse reminders and survey launch communications
