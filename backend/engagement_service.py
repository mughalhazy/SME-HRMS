from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from audit_service.service import emit_audit_record
from event_contract import EventRegistry, emit_canonical_event
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id


class EngagementServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            'error': {
                'code': code,
                'message': message,
                'details': details or [],
                'trace_id': trace_id,
            }
        }


@dataclass(slots=True)
class EmployeeSnapshot:
    tenant_id: str
    employee_id: str
    employee_number: str
    full_name: str
    department_id: str
    department_name: str
    manager_employee_id: str | None
    status: str = 'Active'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SurveyQuestion:
    question_id: str
    prompt: str
    dimension: str
    kind: str
    required: bool
    scale_min: int
    scale_max: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Survey:
    tenant_id: str
    survey_id: str
    code: str
    title: str
    description: str
    status: str
    owner_employee_id: str
    target_department_id: str | None
    questions: list[SurveyQuestion]
    published_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'survey_id': self.survey_id,
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'owner_employee_id': self.owner_employee_id,
            'target_department_id': self.target_department_id,
            'questions': [question.to_dict() for question in self.questions],
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass(slots=True)
class SurveyAnswer:
    question_id: str
    score: int
    comment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SurveyResponse:
    tenant_id: str
    response_id: str
    survey_id: str
    employee_id: str
    answers: list[SurveyAnswer]
    overall_comment: str | None
    sentiment_score: float
    sentiment_label: str
    submitted_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'response_id': self.response_id,
            'survey_id': self.survey_id,
            'employee_id': self.employee_id,
            'answers': [answer.to_dict() for answer in self.answers],
            'overall_comment': self.overall_comment,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'submitted_at': self.submitted_at.isoformat(),
        }


@dataclass(slots=True)
class AggregatedSurveyResult:
    tenant_id: str
    survey_id: str
    response_count: int
    participant_count: int
    target_population: int
    participation_rate: float
    overall_average_score: float
    favorable_ratio: float
    question_scores: list[dict[str, Any]]
    dimension_scores: list[dict[str, Any]]
    score_distribution: dict[str, int]
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['generated_at'] = self.generated_at.isoformat()
        return payload


class EngagementService:
    SURVEY_STATUSES = {'Draft', 'Open', 'Closed'}
    QUESTION_KINDS = {'Likert5'}
    DIMENSIONS = {'D1', 'D2', 'D3', 'D4', 'D5'}
    FAVORABLE_THRESHOLD = 4
    POSITIVE_TERMS = {'great', 'strong', 'supportive', 'excellent', 'growth', 'happy', 'clear', 'confident'}
    NEGATIVE_TERMS = {'burnout', 'stressed', 'blocked', 'poor', 'frustrated', 'unclear', 'overloaded', 'toxic'}

    def __init__(self, db_path: str | None = None) -> None:
        self.employee_snapshots = PersistentKVStore[str, EmployeeSnapshot](service='engagement-service', namespace='employee_snapshots', db_path=db_path)
        shared_db_path = self.employee_snapshots.db_path
        self.surveys = PersistentKVStore[str, Survey](service='engagement-service', namespace='surveys', db_path=shared_db_path)
        self.responses = PersistentKVStore[str, SurveyResponse](service='engagement-service', namespace='responses', db_path=shared_db_path)
        self.aggregated_results = PersistentKVStore[str, AggregatedSurveyResult](service='engagement-service', namespace='aggregated_results', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.tenant_id = DEFAULT_TENANT_ID
        self.event_registry = EventRegistry()
        self.error_logger = CentralErrorLogger('engagement-service')
        self.observability = Observability('engagement-service')
        self._lock = RLock()

    def register_employee_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        snapshot = EmployeeSnapshot(
            tenant_id=tenant_id,
            employee_id=str(payload['employee_id']),
            employee_number=str(payload.get('employee_number') or payload['employee_id']),
            full_name=str(payload['full_name']),
            department_id=str(payload['department_id']),
            department_name=str(payload.get('department_name') or payload['department_id']),
            manager_employee_id=str(payload['manager_employee_id']) if payload.get('manager_employee_id') else None,
            status=str(payload.get('status') or 'Active'),
        )
        self.employee_snapshots[snapshot.employee_id] = snapshot
        return snapshot.to_dict()

    def create_survey(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        owner = self._require_employee(payload['owner_employee_id'], tenant_id=tenant_id, field='owner_employee_id')
        code = str(payload['code']).strip()
        title = str(payload['title']).strip()
        if not code:
            raise self._error(422, 'VALIDATION_ERROR', 'code is required', trace, [{'field': 'code', 'reason': 'must be a non-empty string'}])
        if not title:
            raise self._error(422, 'VALIDATION_ERROR', 'title is required', trace, [{'field': 'title', 'reason': 'must be a non-empty string'}])
        if any(survey.tenant_id == tenant_id and survey.code == code for survey in self.surveys.values()):
            raise self._error(409, 'CONFLICT', 'survey code already exists', trace)

        target_department_id = str(payload['target_department_id']).strip() if payload.get('target_department_id') else None
        if target_department_id and not any(
            snapshot.tenant_id == tenant_id and snapshot.department_id == target_department_id
            for snapshot in self.employee_snapshots.values()
        ):
            raise self._error(422, 'VALIDATION_ERROR', 'target_department_id was not found in employee-service read model', trace, [{'field': 'target_department_id', 'reason': 'unknown department'}])

        questions = self._parse_questions(payload.get('questions'), trace)
        now = self._now()
        survey = Survey(
            tenant_id=tenant_id,
            survey_id=str(uuid4()),
            code=code,
            title=title,
            description=str(payload.get('description') or '').strip(),
            status='Draft',
            owner_employee_id=owner.employee_id,
            target_department_id=target_department_id,
            questions=questions,
            published_at=None,
            closed_at=None,
            created_at=now,
            updated_at=now,
        )
        self.surveys[survey.survey_id] = survey
        self._audit('engagement_survey_created', 'Survey', survey.survey_id, {}, survey.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('EngagementSurveyCreated', {'survey_id': survey.survey_id, 'code': survey.code, 'status': survey.status, 'owner_employee_id': survey.owner_employee_id}, tenant_id=tenant_id, correlation_id=trace)
        payload = self._survey_payload(survey)
        self.observability.track('create_survey', trace_id=trace, started_at=started, success=True, context={'status': 201})
        return 201, payload

    def publish_survey(self, survey_id: str, *, tenant_id: str | None = None, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = trace_id or self.observability.trace_id()
        survey = self._get_survey_record(survey_id, tenant_id=tenant_id)
        if survey.status != 'Draft':
            raise self._error(409, 'INVALID_STATE', 'survey must be Draft before publish', trace)
        before = survey.to_dict()
        survey.status = 'Open'
        survey.published_at = self._now()
        survey.updated_at = survey.published_at
        self.surveys[survey_id] = survey
        after = self._survey_payload(survey)
        self._audit('engagement_survey_published', 'Survey', survey.survey_id, before, after, actor_id=actor_id, actor_type=actor_type, tenant_id=survey.tenant_id, trace_id=trace)
        self._emit('EngagementSurveyPublished', {'survey_id': survey.survey_id, 'status': survey.status, 'published_at': survey.published_at.isoformat()}, tenant_id=survey.tenant_id, correlation_id=trace)
        return 200, after

    def close_survey(self, survey_id: str, *, tenant_id: str | None = None, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = trace_id or self.observability.trace_id()
        survey = self._get_survey_record(survey_id, tenant_id=tenant_id)
        if survey.status != 'Open':
            raise self._error(409, 'INVALID_STATE', 'survey must be Open before close', trace)
        before = survey.to_dict()
        survey.status = 'Closed'
        survey.closed_at = self._now()
        survey.updated_at = survey.closed_at
        self.surveys[survey_id] = survey
        aggregate = self._rebuild_aggregate(survey, trace_id=trace)
        after = self._survey_payload(survey, aggregate=aggregate)
        self._audit('engagement_survey_closed', 'Survey', survey.survey_id, before, after, actor_id=actor_id, actor_type=actor_type, tenant_id=survey.tenant_id, trace_id=trace)
        self._emit('EngagementSurveyClosed', {'survey_id': survey.survey_id, 'status': survey.status, 'closed_at': survey.closed_at.isoformat()}, tenant_id=survey.tenant_id, correlation_id=trace)
        return 200, after

    def submit_response(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        survey = self._get_survey_record(str(payload['survey_id']), tenant_id=tenant_id)
        if survey.status != 'Open':
            raise self._error(409, 'INVALID_STATE', 'survey must be Open before responses can be submitted', trace)
        employee = self._require_employee(payload['employee_id'], tenant_id=tenant_id, field='employee_id')
        if employee.status == 'Terminated':
            raise self._error(422, 'VALIDATION_ERROR', 'terminated employees cannot submit engagement responses', trace, [{'field': 'employee_id', 'reason': 'employee must be active'}])
        if survey.target_department_id and employee.department_id != survey.target_department_id:
            raise self._error(403, 'FORBIDDEN', 'employee is outside the target population for this survey', trace)
        if any(
            response.tenant_id == tenant_id and response.survey_id == survey.survey_id and response.employee_id == employee.employee_id
            for response in self.responses.values()
        ):
            raise self._error(409, 'CONFLICT', 'employee has already responded to this survey', trace)

        answers = self._parse_answers(payload.get('answers'), survey, trace)
        now = self._now()
        response = SurveyResponse(
            tenant_id=tenant_id,
            response_id=str(uuid4()),
            survey_id=survey.survey_id,
            employee_id=employee.employee_id,
            answers=answers,
            overall_comment=str(payload.get('overall_comment')).strip() if payload.get('overall_comment') else None,
            sentiment_score=0.0,
            sentiment_label='neutral',
            submitted_at=now,
        )
        response.sentiment_score = self._sentiment_score(response.overall_comment)
        response.sentiment_label = self._sentiment_label(response.sentiment_score)
        self.responses[response.response_id] = response
        aggregate = self._rebuild_aggregate(survey, trace_id=trace)
        response_payload = self._response_payload(response)
        self._audit('engagement_response_submitted', 'SurveyResponse', response.response_id, {}, response_payload, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('EngagementSurveyResponseSubmitted', {'survey_id': survey.survey_id, 'response_id': response.response_id, 'employee_id': response.employee_id}, tenant_id=tenant_id, correlation_id=trace)
        self.observability.track('submit_response', trace_id=trace, started_at=started, success=True, context={'status': 201})
        return 201, {**response_payload, 'aggregate': aggregate.to_dict()}

    def get_survey(self, survey_id: str, *, tenant_id: str | None = None) -> tuple[int, dict[str, Any]]:
        survey = self._get_survey_record(survey_id, tenant_id=tenant_id)
        aggregate = self.aggregated_results.get(survey.survey_id)
        return 200, self._survey_payload(survey, aggregate=aggregate)

    def list_surveys(self, *, tenant_id: str | None = None, status: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        if status and status not in self.SURVEY_STATUSES:
            raise self._error(422, 'VALIDATION_ERROR', 'invalid survey status', self.observability.trace_id(), [{'field': 'status', 'reason': f'must be one of {sorted(self.SURVEY_STATUSES)}'}])
        rows = [survey for survey in self.surveys.values() if survey.tenant_id == tenant]
        if status:
            rows = [survey for survey in rows if survey.status == status]
        rows.sort(key=lambda item: (item.updated_at.isoformat(), item.survey_id), reverse=True)
        return 200, {'tenant_id': tenant, 'items': [self._survey_payload(survey) for survey in rows]}

    def list_responses(self, survey_id: str, *, tenant_id: str | None = None) -> tuple[int, dict[str, Any]]:
        survey = self._get_survey_record(survey_id, tenant_id=tenant_id)
        rows = [response for response in self.responses.values() if response.tenant_id == survey.tenant_id and response.survey_id == survey.survey_id]
        rows.sort(key=lambda item: (item.submitted_at.isoformat(), item.response_id))
        return 200, {'tenant_id': survey.tenant_id, 'survey_id': survey.survey_id, 'items': [self._response_payload(row) for row in rows]}

    def get_aggregated_results(self, survey_id: str, *, tenant_id: str | None = None) -> tuple[int, dict[str, Any]]:
        survey = self._get_survey_record(survey_id, tenant_id=tenant_id)
        aggregate = self.aggregated_results.get(survey.survey_id)
        if aggregate is None:
            aggregate = self._rebuild_aggregate(survey, trace_id=self.observability.trace_id())
        return 200, {'tenant_id': survey.tenant_id, 'survey_id': survey.survey_id, 'survey': self._survey_payload(survey), 'aggregate': aggregate.to_dict()}

    def get_sentiment_trends(self, *, tenant_id: str | None = None, department_id: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        trends: dict[str, dict[str, Any]] = {}
        for response in self.responses.values():
            if response.tenant_id != tenant:
                continue
            employee = self.employee_snapshots.get(response.employee_id)
            if employee is None or (department_id and employee.department_id != department_id):
                continue
            survey = self.surveys.get(response.survey_id)
            period = (survey.published_at or response.submitted_at).date().isoformat()[:7] if survey else response.submitted_at.date().isoformat()[:7]
            bucket = trends.setdefault(period, {'period': period, 'responses': 0, 'average_sentiment_score': 0.0, 'positive': 0, 'neutral': 0, 'negative': 0})
            bucket['responses'] += 1
            bucket['average_sentiment_score'] += response.sentiment_score
            bucket[response.sentiment_label] += 1
        items = []
        for period, row in sorted(trends.items()):
            responses = row['responses'] or 1
            row['average_sentiment_score'] = round(row['average_sentiment_score'] / responses, 4)
            row['sentiment_index'] = round((row['positive'] - row['negative']) / responses, 4)
            items.append(row)
        return 200, {'tenant_id': tenant, 'department_id': department_id, 'items': items}

    def get_engagement_dashboard(self, *, tenant_id: str | None = None, department_id: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        surveys = [survey for survey in self.surveys.values() if survey.tenant_id == tenant and (department_id is None or survey.target_department_id in {None, department_id})]
        latest_survey = max(surveys, key=lambda item: item.updated_at, default=None)
        trend_status, trends = self.get_sentiment_trends(tenant_id=tenant, department_id=department_id)
        assert trend_status == 200
        latest_trend = trends['items'][-1] if trends['items'] else {'average_sentiment_score': 0.0, 'sentiment_index': 0.0, 'responses': 0}
        return 200, {
            'tenant_id': tenant,
            'department_id': department_id,
            'snapshot': {
                'survey_count': len(surveys),
                'open_surveys': len([survey for survey in surveys if survey.status == 'Open']),
                'closed_surveys': len([survey for survey in surveys if survey.status == 'Closed']),
                'latest_survey_id': latest_survey.survey_id if latest_survey else None,
                'latest_sentiment_score': latest_trend['average_sentiment_score'],
                'latest_sentiment_index': latest_trend['sentiment_index'],
                'latest_response_count': latest_trend['responses'],
            },
            'sentiment_trends': trends['items'],
        }

    def _parse_questions(self, raw_questions: Any, trace_id: str) -> list[SurveyQuestion]:
        if not isinstance(raw_questions, list) or not raw_questions:
            raise self._error(422, 'VALIDATION_ERROR', 'questions are required', trace_id, [{'field': 'questions', 'reason': 'must contain at least one survey question'}])
        questions: list[SurveyQuestion] = []
        seen_prompts: set[str] = set()
        for index, raw in enumerate(raw_questions):
            if not isinstance(raw, dict):
                raise self._error(422, 'VALIDATION_ERROR', 'invalid question payload', trace_id, [{'field': f'questions[{index}]', 'reason': 'must be an object'}])
            prompt = str(raw.get('prompt') or '').strip()
            dimension = str(raw.get('dimension') or '').strip().upper()
            kind = str(raw.get('kind') or 'Likert5').strip()
            if not prompt:
                raise self._error(422, 'VALIDATION_ERROR', 'question prompt is required', trace_id, [{'field': f'questions[{index}].prompt', 'reason': 'must be a non-empty string'}])
            if prompt.lower() in seen_prompts:
                raise self._error(422, 'VALIDATION_ERROR', 'duplicate survey question prompt', trace_id, [{'field': f'questions[{index}].prompt', 'reason': 'must be unique within the survey'}])
            if dimension not in self.DIMENSIONS:
                raise self._error(422, 'VALIDATION_ERROR', 'invalid survey dimension', trace_id, [{'field': f'questions[{index}].dimension', 'reason': f'must be one of {sorted(self.DIMENSIONS)}'}])
            if kind not in self.QUESTION_KINDS:
                raise self._error(422, 'VALIDATION_ERROR', 'invalid question kind', trace_id, [{'field': f'questions[{index}].kind', 'reason': f'must be one of {sorted(self.QUESTION_KINDS)}'}])
            scale_min = int(raw.get('scale_min', 1))
            scale_max = int(raw.get('scale_max', 5))
            if scale_min != 1 or scale_max != 5:
                raise self._error(422, 'VALIDATION_ERROR', 'engagement surveys currently support a 1-5 scale only', trace_id, [{'field': f'questions[{index}]', 'reason': 'scale_min must be 1 and scale_max must be 5'}])
            seen_prompts.add(prompt.lower())
            questions.append(
                SurveyQuestion(
                    question_id=str(raw.get('question_id') or uuid4()),
                    prompt=prompt,
                    dimension=dimension,
                    kind=kind,
                    required=bool(raw.get('required', True)),
                    scale_min=scale_min,
                    scale_max=scale_max,
                )
            )
        return questions

    def _parse_answers(self, raw_answers: Any, survey: Survey, trace_id: str) -> list[SurveyAnswer]:
        if not isinstance(raw_answers, list) or not raw_answers:
            raise self._error(422, 'VALIDATION_ERROR', 'answers are required', trace_id, [{'field': 'answers', 'reason': 'must contain at least one answer'}])
        questions_by_id = {question.question_id: question for question in survey.questions}
        answers: list[SurveyAnswer] = []
        seen_question_ids: set[str] = set()
        for index, raw in enumerate(raw_answers):
            if not isinstance(raw, dict):
                raise self._error(422, 'VALIDATION_ERROR', 'invalid answer payload', trace_id, [{'field': f'answers[{index}]', 'reason': 'must be an object'}])
            question_id = str(raw.get('question_id') or '').strip()
            question = questions_by_id.get(question_id)
            if question is None:
                raise self._error(422, 'VALIDATION_ERROR', 'answer references unknown survey question', trace_id, [{'field': f'answers[{index}].question_id', 'reason': 'must belong to the survey'}])
            if question_id in seen_question_ids:
                raise self._error(422, 'VALIDATION_ERROR', 'duplicate answer for survey question', trace_id, [{'field': f'answers[{index}].question_id', 'reason': 'must be unique'}])
            score = int(raw.get('score'))
            if score < question.scale_min or score > question.scale_max:
                raise self._error(422, 'VALIDATION_ERROR', 'score is out of range', trace_id, [{'field': f'answers[{index}].score', 'reason': f'must be between {question.scale_min} and {question.scale_max}'}])
            seen_question_ids.add(question_id)
            answers.append(SurveyAnswer(question_id=question_id, score=score, comment=str(raw.get('comment')).strip() if raw.get('comment') else None))
        required_ids = {question.question_id for question in survey.questions if question.required}
        if not required_ids.issubset(seen_question_ids):
            missing = sorted(required_ids - seen_question_ids)
            raise self._error(422, 'VALIDATION_ERROR', 'required survey questions are unanswered', trace_id, [{'field': 'answers', 'reason': f'missing question_ids: {missing}'}])
        return answers

    def _rebuild_aggregate(self, survey: Survey, *, trace_id: str) -> AggregatedSurveyResult:
        relevant_responses = [
            response
            for response in self.responses.values()
            if response.tenant_id == survey.tenant_id and response.survey_id == survey.survey_id
        ]
        relevant_responses.sort(key=lambda item: (item.submitted_at.isoformat(), item.response_id))
        target_population = len(self._target_population(survey))
        question_lookup = {question.question_id: question for question in survey.questions}
        score_distribution = {str(score): 0 for score in range(1, 6)}
        total_score = 0
        total_answers = 0
        favorable_answers = 0
        question_scores: list[dict[str, Any]] = []
        dimension_scores: list[dict[str, Any]] = []

        answer_sets: dict[str, list[int]] = {question.question_id: [] for question in survey.questions}
        for response in relevant_responses:
            for answer in response.answers:
                answer_sets.setdefault(answer.question_id, []).append(answer.score)
                score_distribution[str(answer.score)] = score_distribution.get(str(answer.score), 0) + 1
                total_score += answer.score
                total_answers += 1
                if answer.score >= self.FAVORABLE_THRESHOLD:
                    favorable_answers += 1

        for question in survey.questions:
            scores = answer_sets.get(question.question_id, [])
            question_scores.append({
                'question_id': question.question_id,
                'prompt': question.prompt,
                'dimension': question.dimension,
                'response_count': len(scores),
                'average_score': round(sum(scores) / len(scores), 2) if scores else 0.0,
                'favorable_ratio': round(sum(1 for score in scores if score >= self.FAVORABLE_THRESHOLD) / len(scores), 4) if scores else 0.0,
            })

        for dimension in sorted(self.DIMENSIONS):
            dimension_question_ids = [question.question_id for question in survey.questions if question.dimension == dimension]
            scores = [score for question_id in dimension_question_ids for score in answer_sets.get(question_id, [])]
            dimension_scores.append({
                'dimension': dimension,
                'question_count': len(dimension_question_ids),
                'response_count': len(scores),
                'average_score': round(sum(scores) / len(scores), 2) if scores else 0.0,
                'favorable_ratio': round(sum(1 for score in scores if score >= self.FAVORABLE_THRESHOLD) / len(scores), 4) if scores else 0.0,
            })

        aggregate = AggregatedSurveyResult(
            tenant_id=survey.tenant_id,
            survey_id=survey.survey_id,
            response_count=len(relevant_responses),
            participant_count=len({response.employee_id for response in relevant_responses}),
            target_population=target_population,
            participation_rate=round(len(relevant_responses) / target_population, 4) if target_population else 0.0,
            overall_average_score=round(total_score / total_answers, 2) if total_answers else 0.0,
            favorable_ratio=round(favorable_answers / total_answers, 4) if total_answers else 0.0,
            question_scores=question_scores,
            dimension_scores=dimension_scores,
            score_distribution=score_distribution,
            generated_at=self._now(),
        )
        self.aggregated_results[survey.survey_id] = aggregate
        self._audit('engagement_results_aggregated', 'SurveyAggregate', survey.survey_id, {}, aggregate.to_dict(), actor_id='system', actor_type='system', tenant_id=survey.tenant_id, trace_id=trace_id)
        self._emit('EngagementSurveyResultsAggregated', {
            'survey_id': survey.survey_id,
            'response_count': aggregate.response_count,
            'participation_rate': aggregate.participation_rate,
            'overall_average_score': aggregate.overall_average_score,
        }, tenant_id=survey.tenant_id, correlation_id=trace_id)
        return aggregate

    def _target_population(self, survey: Survey) -> list[EmployeeSnapshot]:
        rows = [
            snapshot
            for snapshot in self.employee_snapshots.values()
            if snapshot.tenant_id == survey.tenant_id and snapshot.status != 'Terminated'
        ]
        if survey.target_department_id:
            rows = [snapshot for snapshot in rows if snapshot.department_id == survey.target_department_id]
        rows.sort(key=lambda item: (item.department_id, item.full_name, item.employee_id))
        return rows

    def _survey_payload(self, survey: Survey, *, aggregate: AggregatedSurveyResult | None = None) -> dict[str, Any]:
        owner = self._require_employee(survey.owner_employee_id, tenant_id=survey.tenant_id, field='owner_employee_id')
        payload = {**survey.to_dict(), 'owner': owner.to_dict()}
        if aggregate is not None:
            payload['aggregate'] = aggregate.to_dict()
        return payload

    def _response_payload(self, response: SurveyResponse) -> dict[str, Any]:
        employee = self._require_employee(response.employee_id, tenant_id=response.tenant_id, field='employee_id')
        payload = response.to_dict()
        payload['employee'] = employee.to_dict()
        return payload

    def _get_survey_record(self, survey_id: str, *, tenant_id: str | None = None) -> Survey:
        survey = self.surveys.get(survey_id)
        if survey is None:
            raise self._error(404, 'NOT_FOUND', 'survey was not found', self.observability.trace_id())
        if tenant_id is not None:
            assert_tenant_access(survey.tenant_id, normalize_tenant_id(tenant_id))
        return survey

    def _require_employee(self, employee_id: str | None, *, tenant_id: str, field: str) -> EmployeeSnapshot:
        if not employee_id:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is required', self.observability.trace_id(), [{'field': field, 'reason': 'must be provided'}])
        snapshot = self.employee_snapshots.get(str(employee_id))
        if snapshot is None or snapshot.tenant_id != tenant_id:
            raise self._error(404, 'NOT_FOUND', f'{field} was not found in employee-service read model', self.observability.trace_id())
        return snapshot

    def _audit(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, actor_id: str, actor_type: str, tenant_id: str, trace_id: str) -> None:
        emit_audit_record(
            service_name='engagement-service',
            tenant_id=tenant_id,
            actor={'id': actor_id, 'type': actor_type},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'bounded_context': 'engagement-management'},
        )

    def _emit(self, legacy_event_name: str, data: dict[str, Any], *, tenant_id: str, correlation_id: str | None) -> None:
        identity = data.get('survey_id') or data.get('response_id') or str(uuid4())
        idempotency_key = f"{identity}:{json.dumps(data, sort_keys=True, default=str)}"
        emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data={'tenant_id': tenant_id, **data},
            source='engagement-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

    def _error(self, status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> EngagementServiceError:
        error = EngagementServiceError(status_code, code, message, trace_id, details)
        self.error_logger.log(
            'engagement.error',
            error,
            trace_id=trace_id,
            details={'status': status_code, 'code': code, 'details': details or []},
        )
        return error

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _sentiment_score(self, comment: str | None) -> float:
        if not comment:
            return 0.0
        tokens = [token.strip('.,!?').lower() for token in comment.split() if token.strip()]
        if not tokens:
            return 0.0
        positive = sum(1 for token in tokens if token in self.POSITIVE_TERMS)
        negative = sum(1 for token in tokens if token in self.NEGATIVE_TERMS)
        return round((positive - negative) / len(tokens), 4)

    @staticmethod
    def _sentiment_label(score: float) -> str:
        if score > 0.05:
            return 'positive'
        if score < -0.05:
            return 'negative'
        return 'neutral'
