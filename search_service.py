from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Iterable, Mapping
from uuid import uuid4

from event_contract import normalize_event_type
from persistent_store import PersistentKVStore
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id


class SearchServiceError(ValueError):
    def __init__(self, status_code: int, code: str, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


@dataclass(slots=True)
class SearchDocument:
    document_id: str
    tenant_id: str
    source_view: str
    source_key: str
    domain: str
    entity_type: str
    display_name: str
    search_blob: str
    keywords: list[str] = field(default_factory=list)
    department_id: str | None = None
    department_name: str | None = None
    role_id: str | None = None
    role_title: str | None = None
    status: str | None = None
    sort_name: str = ''
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SOURCE_MODEL_CONFIG: dict[str, dict[str, Any]] = {
    'employee_directory_view': {
        'key_fields': ('employee_id',),
        'domain': 'employees',
        'job_scope': 'row',
    },
    'organization_structure_view': {
        'key_fields': ('department_id', 'employee_id'),
        'domain': 'organization',
        'job_scope': 'model',
    },
    'candidate_pipeline_view': {
        'key_fields': ('candidate_id',),
        'domain': 'hiring',
        'job_scope': 'row',
    },
    'document_library_view': {
        'key_fields': ('document_id',),
        'domain': 'documents',
        'job_scope': 'row',
    },
    'payroll_summary_view': {
        'key_fields': ('payroll_record_id',),
        'domain': 'payroll',
        'job_scope': 'model',
    },
}

EVENT_MODEL_MAP: dict[str, tuple[str, ...]] = {
    'employee.created': ('employee_directory_view', 'organization_structure_view'),
    'employee.updated': ('employee_directory_view', 'organization_structure_view'),
    'employee.status.changed': ('employee_directory_view', 'organization_structure_view'),
    'department.created': ('organization_structure_view',),
    'department.updated': ('organization_structure_view',),
    'role.created': ('organization_structure_view',),
    'role.updated': ('organization_structure_view',),
    'hiring.candidate.applied': ('candidate_pipeline_view',),
    'hiring.candidate.stage.changed': ('candidate_pipeline_view',),
    'hiring.interview.scheduled': ('candidate_pipeline_view',),
    'hiring.interview.completed': ('candidate_pipeline_view',),
    'hiring.interview.calendar.synced': ('candidate_pipeline_view',),
    'hiring.candidate.hired': ('candidate_pipeline_view', 'employee_directory_view', 'organization_structure_view'),
    'payroll.record.processed': ('payroll_summary_view',),
    'payroll.record.paid': ('payroll_summary_view',),
    'payroll.record.cancelled': ('payroll_summary_view',),
    'employee.document.stored': ('document_library_view',),
    'employee.document.updated': ('document_library_view',),
}

LEGACY_EVENT_OVERRIDES = {
    'DocumentStored': 'employee.document.stored',
    'DocumentUpdated': 'employee.document.updated',
}


class SearchIndexingService:
    """Projection-backed, tenant-safe search/indexing service.

    The service never queries transactional domain stores for search queries. It only reads
    source read models that have been ingested into its own projection store and serves search
    responses from `search_documents`.
    """

    DEFAULT_LIMIT = 25
    MAX_LIMIT = 100

    def __init__(self, db_path: str | None = None) -> None:
        self.source_rows = PersistentKVStore[str, dict[str, Any]](service='search-service', namespace='source_rows', db_path=db_path)
        self.index_documents = PersistentKVStore[str, SearchDocument](service='search-service', namespace='index_documents', db_path=db_path)
        self.processed_events = PersistentKVStore[str, dict[str, Any]](service='search-service', namespace='processed_events', db_path=db_path)
        self.projection_state = PersistentKVStore[str, dict[str, Any]](service='search-service', namespace='projection_state', db_path=db_path)
        self.query_audit = PersistentKVStore[str, dict[str, Any]](service='search-service', namespace='query_audit', db_path=db_path)
        self._lock = RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_string(value: Any) -> str:
        return str(value or '').strip()

    def _tenant(self, tenant_id: str | None) -> str:
        return normalize_tenant_id(tenant_id)

    def _model_config(self, model_name: str) -> dict[str, Any]:
        config = SOURCE_MODEL_CONFIG.get(model_name)
        if config is None:
            raise SearchServiceError(422, 'UNSUPPORTED_READ_MODEL', f'{model_name} is not a supported read model')
        return config

    def _row_key(self, model_name: str, row: Mapping[str, Any]) -> str:
        config = self._model_config(model_name)
        tenant = self._tenant(row.get('tenant_id'))
        values: list[str] = []
        missing: list[str] = []
        for field in config['key_fields']:
            value = self._normalize_string(row.get(field))
            if not value:
                missing.append(field)
            values.append(value)
        if missing:
            raise SearchServiceError(
                422,
                'INVALID_READ_MODEL_ROW',
                f'{model_name} rows require key fields: {", ".join(config["key_fields"])}',
                details=[{'field': field, 'reason': 'is required'} for field in missing],
            )
        return f"{tenant}:{model_name}:{':'.join(values)}"

    def ingest_read_model(
        self,
        model_name: str,
        rows: Iterable[dict[str, Any]],
        *,
        tenant_id: str | None = None,
        replace: bool = False,
    ) -> dict[str, Any]:
        tenant = self._tenant(tenant_id)
        self._model_config(model_name)
        normalized_rows: dict[str, dict[str, Any]] = {}
        for row in rows:
            payload = dict(row)
            payload['tenant_id'] = self._tenant(payload.get('tenant_id') or tenant)
            key = self._row_key(model_name, payload)
            normalized_rows[key] = payload

        with self._lock:
            if replace:
                prefix = f'{tenant}:{model_name}:'
                for existing_key in [key for key in self.source_rows.keys() if key.startswith(prefix) and key not in normalized_rows]:
                    del self.source_rows[existing_key]
            for key, payload in normalized_rows.items():
                self.source_rows[key] = {
                    'tenant_id': payload['tenant_id'],
                    'model_name': model_name,
                    'row_key': key,
                    'row': payload,
                    'updated_at': self._now(),
                }
            self.projection_state[f'read_model:{tenant}:{model_name}'] = {
                'tenant_id': tenant,
                'model_name': model_name,
                'row_count': len([key for key in self.source_rows.keys() if key.startswith(f'{tenant}:{model_name}:')]),
                'last_ingested_at': self._now(),
                'replace': replace,
            }
        return {'tenant_id': tenant, 'model_name': model_name, 'row_count': len(normalized_rows), 'replace': replace}

    def _read_model_rows(self, tenant_id: str, model_name: str) -> list[dict[str, Any]]:
        prefix = f'{tenant_id}:{model_name}:'
        rows = [
            dict(item['row'])
            for key, item in self.source_rows.items()
            if key.startswith(prefix)
        ]
        rows.sort(key=lambda row: tuple(self._normalize_string(row.get(field)) for field in SOURCE_MODEL_CONFIG[model_name]['key_fields']))
        return rows

    def _index_doc_id(self, tenant_id: str, source_view: str, entity_type: str, source_key: str) -> str:
        return f'{tenant_id}:{source_view}:{entity_type}:{source_key}'

    def _replace_index_docs(self, *, tenant_id: str, source_view: str, documents: list[SearchDocument]) -> None:
        prefix = f'{tenant_id}:{source_view}:'
        current_ids = {document.document_id for document in documents}
        for document_id in [key for key in self.index_documents.keys() if key.startswith(prefix) and key not in current_ids]:
            del self.index_documents[document_id]
        for document in documents:
            self.index_documents[document.document_id] = document
        self.projection_state[f'index:{tenant_id}:{source_view}'] = {
            'tenant_id': tenant_id,
            'source_view': source_view,
            'document_count': len(documents),
            'indexed_at': self._now(),
        }

    def rebuild_index(self, *, tenant_id: str, model_names: Iterable[str] | None = None) -> dict[str, Any]:
        tenant = self._tenant(tenant_id)
        targets = list(model_names or SOURCE_MODEL_CONFIG.keys())
        indexed_counts: dict[str, int] = {}
        with self._lock:
            for model_name in targets:
                self._model_config(model_name)
                rows = self._read_model_rows(tenant, model_name)
                documents = self._build_documents(model_name, tenant, rows)
                self._replace_index_docs(tenant_id=tenant, source_view=model_name, documents=documents)
                indexed_counts[model_name] = len(documents)
            self.projection_state[f'global_index:{tenant}'] = {
                'tenant_id': tenant,
                'indexed_models': targets,
                'indexed_counts': indexed_counts,
                'updated_at': self._now(),
            }
        return {'tenant_id': tenant, 'indexed_counts': indexed_counts, 'indexed_models': targets}

    def _build_documents(self, model_name: str, tenant_id: str, rows: list[dict[str, Any]]) -> list[SearchDocument]:
        if model_name == 'employee_directory_view':
            return self._employee_documents(tenant_id, rows)
        if model_name == 'organization_structure_view':
            return self._organization_documents(tenant_id, rows)
        if model_name == 'candidate_pipeline_view':
            return self._candidate_documents(tenant_id, rows)
        if model_name == 'document_library_view':
            return self._document_documents(tenant_id, rows)
        if model_name == 'payroll_summary_view':
            return self._payroll_run_documents(tenant_id, rows)
        raise SearchServiceError(422, 'UNSUPPORTED_READ_MODEL', f'{model_name} is not a supported read model')

    def _employee_documents(self, tenant_id: str, rows: list[dict[str, Any]]) -> list[SearchDocument]:
        documents: list[SearchDocument] = []
        for row in rows:
            employee_id = self._normalize_string(row.get('employee_id'))
            full_name = self._normalize_string(row.get('full_name') or row.get('employee_name'))
            department_name = self._normalize_string(row.get('department_name'))
            role_title = self._normalize_string(row.get('role_title'))
            blob_parts = [
                full_name,
                self._normalize_string(row.get('employee_number')),
                self._normalize_string(row.get('email')),
                self._normalize_string(row.get('phone')),
                department_name,
                role_title,
                self._normalize_string(row.get('manager_name')),
                self._normalize_string(row.get('employment_type')),
                self._normalize_string(row.get('employee_status') or row.get('status')),
            ]
            metadata = {
                'employee_id': employee_id,
                'employee_number': row.get('employee_number'),
                'email': row.get('email'),
                'phone': row.get('phone'),
                'manager_employee_id': row.get('manager_employee_id'),
                'manager_name': row.get('manager_name'),
                'hire_date': row.get('hire_date'),
                'employment_type': row.get('employment_type'),
            }
            documents.append(
                SearchDocument(
                    document_id=self._index_doc_id(tenant_id, 'employee_directory_view', 'employee', employee_id),
                    tenant_id=tenant_id,
                    source_view='employee_directory_view',
                    source_key=employee_id,
                    domain='employees',
                    entity_type='employee',
                    display_name=full_name,
                    search_blob=' '.join(part for part in blob_parts if part).lower(),
                    keywords=[part for part in blob_parts if part],
                    department_id=self._normalize_string(row.get('department_id')) or None,
                    department_name=department_name or None,
                    role_id=self._normalize_string(row.get('role_id')) or None,
                    role_title=role_title or None,
                    status=self._normalize_string(row.get('employee_status') or row.get('status')) or None,
                    sort_name=full_name.lower(),
                    updated_at=self._normalize_string(row.get('updated_at')) or self._now(),
                    metadata=metadata,
                )
            )
        return documents

    def _organization_documents(self, tenant_id: str, rows: list[dict[str, Any]]) -> list[SearchDocument]:
        department_groups: dict[str, dict[str, Any]] = {}
        role_groups: dict[str, dict[str, Any]] = {}
        for row in rows:
            department_id = self._normalize_string(row.get('department_id'))
            if department_id:
                group = department_groups.setdefault(
                    department_id,
                    {
                        'department_id': department_id,
                        'department_name': self._normalize_string(row.get('department_name')),
                        'department_code': self._normalize_string(row.get('department_code')),
                        'status': self._normalize_string(row.get('department_status')),
                        'head_employee_id': self._normalize_string(row.get('head_employee_id')),
                        'head_employee_name': self._normalize_string(row.get('head_employee_name')),
                        'employees': set(),
                        'roles': set(),
                        'updated_at': self._normalize_string(row.get('updated_at')),
                    },
                )
                employee_name = self._normalize_string(row.get('employee_name'))
                role_title = self._normalize_string(row.get('role_title'))
                if employee_name:
                    group['employees'].add(employee_name)
                if role_title:
                    group['roles'].add(role_title)
                group['updated_at'] = max(group['updated_at'], self._normalize_string(row.get('updated_at')))
            role_id = self._normalize_string(row.get('role_id'))
            if role_id:
                role_group = role_groups.setdefault(
                    role_id,
                    {
                        'role_id': role_id,
                        'role_title': self._normalize_string(row.get('role_title')),
                        'departments': set(),
                        'employees': set(),
                        'status': self._normalize_string(row.get('department_status')),
                        'updated_at': self._normalize_string(row.get('updated_at')),
                    },
                )
                if row.get('department_name'):
                    role_group['departments'].add(self._normalize_string(row.get('department_name')))
                if row.get('employee_name'):
                    role_group['employees'].add(self._normalize_string(row.get('employee_name')))
                role_group['updated_at'] = max(role_group['updated_at'], self._normalize_string(row.get('updated_at')))
        documents: list[SearchDocument] = []
        for department_id, group in department_groups.items():
            keywords = [
                group['department_name'],
                group['department_code'],
                group['head_employee_name'],
                *sorted(group['roles']),
                *sorted(group['employees']),
            ]
            documents.append(
                SearchDocument(
                    document_id=self._index_doc_id(tenant_id, 'organization_structure_view', 'department', department_id),
                    tenant_id=tenant_id,
                    source_view='organization_structure_view',
                    source_key=department_id,
                    domain='organization',
                    entity_type='department',
                    display_name=group['department_name'] or department_id,
                    search_blob=' '.join(part for part in keywords if part).lower(),
                    keywords=[part for part in keywords if part],
                    department_id=department_id,
                    department_name=group['department_name'] or None,
                    status=group['status'] or None,
                    sort_name=(group['department_name'] or department_id).lower(),
                    updated_at=group['updated_at'] or self._now(),
                    metadata={
                        'department_code': group['department_code'],
                        'head_employee_id': group['head_employee_id'],
                        'head_employee_name': group['head_employee_name'],
                        'employee_count': len(group['employees']),
                        'role_count': len(group['roles']),
                    },
                )
            )
        for role_id, group in role_groups.items():
            keywords = [group['role_title'], *sorted(group['departments']), *sorted(group['employees'])]
            documents.append(
                SearchDocument(
                    document_id=self._index_doc_id(tenant_id, 'organization_structure_view', 'role', role_id),
                    tenant_id=tenant_id,
                    source_view='organization_structure_view',
                    source_key=role_id,
                    domain='organization',
                    entity_type='role',
                    display_name=group['role_title'] or role_id,
                    search_blob=' '.join(part for part in keywords if part).lower(),
                    keywords=[part for part in keywords if part],
                    role_id=role_id,
                    role_title=group['role_title'] or None,
                    status=group['status'] or None,
                    sort_name=(group['role_title'] or role_id).lower(),
                    updated_at=group['updated_at'] or self._now(),
                    metadata={
                        'department_names': sorted(group['departments']),
                        'employee_count': len(group['employees']),
                    },
                )
            )
        return documents

    def _candidate_documents(self, tenant_id: str, rows: list[dict[str, Any]]) -> list[SearchDocument]:
        documents: list[SearchDocument] = []
        for row in rows:
            candidate_id = self._normalize_string(row.get('candidate_id'))
            display_name = self._normalize_string(row.get('candidate_name'))
            job_title = self._normalize_string(row.get('job_title'))
            department_name = self._normalize_string(row.get('department_name'))
            role_title = self._normalize_string(row.get('role_title'))
            stage = self._normalize_string(row.get('pipeline_stage'))
            keywords = [
                display_name,
                self._normalize_string(row.get('candidate_email')),
                job_title,
                department_name,
                role_title,
                stage,
                self._normalize_string(row.get('source')),
                self._normalize_string(row.get('last_interview_recommendation')),
            ]
            documents.append(
                SearchDocument(
                    document_id=self._index_doc_id(tenant_id, 'candidate_pipeline_view', 'candidate', candidate_id),
                    tenant_id=tenant_id,
                    source_view='candidate_pipeline_view',
                    source_key=candidate_id,
                    domain='hiring',
                    entity_type='candidate',
                    display_name=display_name,
                    search_blob=' '.join(part for part in keywords if part).lower(),
                    keywords=[part for part in keywords if part],
                    department_id=self._normalize_string(row.get('department_id')) or None,
                    department_name=department_name or None,
                    role_id=self._normalize_string(row.get('role_id')) or None,
                    role_title=role_title or None,
                    status=stage or None,
                    sort_name=display_name.lower(),
                    updated_at=self._normalize_string(row.get('updated_at') or row.get('stage_updated_at')) or self._now(),
                    metadata={
                        'candidate_id': candidate_id,
                        'candidate_email': row.get('candidate_email'),
                        'job_posting_id': row.get('job_posting_id'),
                        'job_title': row.get('job_title'),
                        'application_date': row.get('application_date'),
                        'next_interview_at': row.get('next_interview_at'),
                        'interview_count': row.get('interview_count'),
                        'source': row.get('source'),
                    },
                )
            )
        return documents

    def _document_documents(self, tenant_id: str, rows: list[dict[str, Any]]) -> list[SearchDocument]:
        documents: list[SearchDocument] = []
        for row in rows:
            document_id = self._normalize_string(row.get('document_id'))
            title = self._normalize_string(row.get('title'))
            document_type = self._normalize_string(row.get('document_type'))
            employee_name = self._normalize_string(row.get('employee_name'))
            department_name = self._normalize_string(row.get('department_name'))
            keywords = [
                title,
                document_type,
                employee_name,
                department_name,
                self._normalize_string(row.get('policy_code')),
                self._normalize_string(row.get('status')),
            ]
            documents.append(
                SearchDocument(
                    document_id=self._index_doc_id(tenant_id, 'document_library_view', 'document', document_id),
                    tenant_id=tenant_id,
                    source_view='document_library_view',
                    source_key=document_id,
                    domain='documents',
                    entity_type='document',
                    display_name=title or document_id,
                    search_blob=' '.join(part for part in keywords if part).lower(),
                    keywords=[part for part in keywords if part],
                    department_id=self._normalize_string(row.get('department_id')) or None,
                    department_name=department_name or None,
                    status=self._normalize_string(row.get('status')) or None,
                    sort_name=(title or document_id).lower(),
                    updated_at=self._normalize_string(row.get('updated_at') or row.get('created_at')) or self._now(),
                    metadata={
                        'document_id': document_id,
                        'document_type': row.get('document_type'),
                        'employee_id': row.get('employee_id'),
                        'employee_name': row.get('employee_name'),
                        'expiry_date': row.get('expiry_date'),
                        'requires_acknowledgement': row.get('requires_acknowledgement'),
                    },
                )
            )
        return documents

    def _payroll_run_documents(self, tenant_id: str, rows: list[dict[str, Any]]) -> list[SearchDocument]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            period_start = self._normalize_string(row.get('pay_period_start'))
            period_end = self._normalize_string(row.get('pay_period_end'))
            status = self._normalize_string(row.get('status'))
            key = f'{period_start}:{period_end}:{status or "unknown"}'
            group = grouped.setdefault(
                key,
                {
                    'period_start': period_start,
                    'period_end': period_end,
                    'status': status,
                    'employee_count': 0,
                    'net_total': 0.0,
                    'departments': set(),
                    'currencies': set(),
                    'updated_at': self._normalize_string(row.get('updated_at')),
                },
            )
            group['employee_count'] += 1
            try:
                group['net_total'] += float(row.get('net_pay') or 0)
            except (TypeError, ValueError):
                group['net_total'] += 0.0
            if row.get('department_name'):
                group['departments'].add(self._normalize_string(row.get('department_name')))
            if row.get('currency'):
                group['currencies'].add(self._normalize_string(row.get('currency')))
            group['updated_at'] = max(group['updated_at'], self._normalize_string(row.get('updated_at')))
        documents: list[SearchDocument] = []
        for source_key, group in grouped.items():
            display_name = f"Payroll run {group['period_start']} to {group['period_end']}"
            keywords = [display_name, group['status'], *sorted(group['departments']), *sorted(group['currencies'])]
            documents.append(
                SearchDocument(
                    document_id=self._index_doc_id(tenant_id, 'payroll_summary_view', 'payroll_run', source_key),
                    tenant_id=tenant_id,
                    source_view='payroll_summary_view',
                    source_key=source_key,
                    domain='payroll',
                    entity_type='payroll_run',
                    display_name=display_name,
                    search_blob=' '.join(part for part in keywords if part).lower(),
                    keywords=[part for part in keywords if part],
                    status=group['status'] or None,
                    sort_name=display_name.lower(),
                    updated_at=group['updated_at'] or self._now(),
                    metadata={
                        'pay_period_start': group['period_start'],
                        'pay_period_end': group['period_end'],
                        'employee_count': group['employee_count'],
                        'net_total': round(group['net_total'], 2),
                        'currencies': sorted(group['currencies']),
                        'department_names': sorted(group['departments']),
                    },
                )
            )
        return documents

    def _normalize_event_name(self, event: Mapping[str, Any]) -> str:
        raw = self._normalize_string(event.get('event_type') or event.get('event_name') or event.get('legacy_event_name') or event.get('type'))
        if not raw:
            raise SearchServiceError(422, 'INVALID_EVENT', 'event_name or event_type is required')
        return normalize_event_type(LEGACY_EVENT_OVERRIDES.get(raw, raw))

    def consume_event(self, event: Mapping[str, Any], *, background_jobs: Any | None = None) -> dict[str, Any]:
        event_id = self._normalize_string(event.get('event_id')) or str(uuid4())
        if self.processed_events.get(event_id) is not None:
            payload = dict(self.processed_events[event_id])
            payload['duplicate'] = True
            return payload
        tenant = self._tenant(event.get('tenant_id'))
        event_type = self._normalize_event_name(event)
        model_names = list(EVENT_MODEL_MAP.get(event_type, ()))
        if not model_names:
            raise SearchServiceError(422, 'UNSUPPORTED_EVENT', f'{event_type} is not supported by search indexing')
        payload = {
            'event_id': event_id,
            'tenant_id': tenant,
            'event_type': event_type,
            'model_names': model_names,
            'occurred_at': self._normalize_string(event.get('timestamp') or event.get('occurred_at')) or self._now(),
            'enqueued_at': self._now(),
        }
        self.processed_events[event_id] = payload
        self.projection_state[f'event:{event_id}'] = payload
        if background_jobs is None:
            result = self.process_reindex_job(payload)
            payload['result'] = result
            return payload
        job = background_jobs.enqueue_job(
            tenant_id=tenant,
            job_type='search.reindex',
            payload={
                'event_id': event_id,
                'tenant_id': tenant,
                'model_names': model_names,
            },
            actor_type='service',
            trace_id=self._normalize_string(event.get('trace_id')) or event_id,
            correlation_id=self._normalize_string(event.get('trace_id')) or event_id,
            idempotency_key=f'search:{tenant}:{event_id}',
        )
        payload['job_id'] = job.job_id
        return payload

    def process_reindex_job(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        tenant = self._tenant(payload.get('tenant_id'))
        model_names = [str(name) for name in payload.get('model_names') or []]
        if not model_names:
            raise SearchServiceError(422, 'INVALID_JOB_PAYLOAD', 'model_names must not be empty')
        return self.rebuild_index(tenant_id=tenant, model_names=model_names)

    def register_background_jobs(self, background_jobs: Any) -> None:
        def handler(context: Any) -> dict[str, Any]:
            return self.process_reindex_job(context.job.payload)

        background_jobs.register_handler('search.reindex', handler, max_attempts=3)

    def list_index_documents(self, *, tenant_id: str, source_view: str | None = None) -> list[dict[str, Any]]:
        tenant = self._tenant(tenant_id)
        rows = [document.to_dict() for document in self.index_documents.values() if document.tenant_id == tenant]
        if source_view is not None:
            rows = [row for row in rows if row['source_view'] == source_view]
        rows.sort(key=lambda row: (row['entity_type'], row['display_name'], row['document_id']))
        return rows

    def search(
        self,
        *,
        tenant_id: str,
        q: str | None = None,
        department_id: str | None = None,
        role_id: str | None = None,
        status: str | None = None,
        entity_types: Iterable[str] | None = None,
        domains: Iterable[str] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        tenant = self._tenant(tenant_id)
        if not tenant:
            raise SearchServiceError(422, 'VALIDATION_ERROR', 'tenant_id is required')
        normalized_limit = self.DEFAULT_LIMIT if limit is None else max(1, min(int(limit), self.MAX_LIMIT))
        offset = int(cursor or '0') if str(cursor or '0').isdigit() else 0
        terms = [part for part in self._normalize_string(q).lower().split() if part]
        entity_type_set = {str(item) for item in (entity_types or []) if str(item)}
        domain_set = {str(item) for item in (domains or []) if str(item)}

        rows = [document.to_dict() for document in self.index_documents.values() if document.tenant_id == tenant]
        if entity_type_set:
            rows = [row for row in rows if row['entity_type'] in entity_type_set]
        if domain_set:
            rows = [row for row in rows if row['domain'] in domain_set]
        if department_id is not None:
            rows = [row for row in rows if row.get('department_id') == department_id]
        if role_id is not None:
            rows = [row for row in rows if row.get('role_id') == role_id]
        if status is not None:
            rows = [row for row in rows if row.get('status') == status]

        for row in rows:
            row['_score'] = self._score_row(row, terms)
        if terms:
            rows = [row for row in rows if row['_score'] > 0]

        rows = self._sort_rows(rows, sort=sort, has_query=bool(terms))
        page = rows[offset:offset + normalized_limit]
        next_cursor = str(offset + normalized_limit) if offset + normalized_limit < len(rows) else None
        for row in page:
            row.pop('_score', None)
        self.query_audit['last_query'] = {
            'tenant_id': tenant,
            'query': q,
            'result_count': len(page),
            'total_count': len(rows),
            'department_id': department_id,
            'role_id': role_id,
            'status': status,
            'entity_types': sorted(entity_type_set),
            'domains': sorted(domain_set),
            'used_index_only': True,
            'executed_at': self._now(),
        }
        return {
            'items': page,
            '_pagination': {
                'limit': normalized_limit,
                'cursor': str(offset),
                'next_cursor': next_cursor,
                'count': len(page),
                'total_count': len(rows),
            },
        }

    def _score_row(self, row: Mapping[str, Any], terms: list[str]) -> int:
        if not terms:
            return 0
        haystack = self._normalize_string(row.get('search_blob')).lower()
        display_name = self._normalize_string(row.get('display_name')).lower()
        score = 0
        for term in terms:
            if term in display_name:
                score += 5
            if haystack.startswith(term):
                score += 3
            if f' {term}' in haystack or haystack.endswith(term):
                score += 2
            if term in haystack:
                score += 1
        return score

    def _sort_rows(self, rows: list[dict[str, Any]], *, sort: str | None, has_query: bool) -> list[dict[str, Any]]:
        fields = [part.strip() for part in str(sort or '').split(',') if part.strip()]
        if not fields:
            fields = ['-updated_at', 'display_name']
            if has_query:
                fields = ['-_score', *fields]
        for field in reversed(fields):
            reverse = field.startswith('-')
            key = field[1:] if reverse else field
            rows.sort(key=lambda row, field_name=key: self._sort_value(row.get(field_name)), reverse=reverse)
        return rows

    @staticmethod
    def _sort_value(value: Any) -> Any:
        if value is None:
            return ''
        if isinstance(value, (int, float)):
            return value
        return str(value).lower()

    def get_projection_state(self, *, tenant_id: str) -> dict[str, Any]:
        tenant = self._tenant(tenant_id)
        states = {
            key: value
            for key, value in self.projection_state.items()
            if value.get('tenant_id') == tenant
        }
        return {
            'tenant_id': tenant,
            'states': states,
            'last_query': self.query_audit.get('last_query'),
        }

    def require_tenant(self, tenant_id: str | None) -> str:
        tenant = self._tenant(tenant_id)
        if not tenant_id:
            raise SearchServiceError(422, 'VALIDATION_ERROR', 'tenant_id is required')
        return tenant

    def assert_document_access(self, document_id: str, *, tenant_id: str) -> dict[str, Any]:
        document = self.index_documents.get(document_id)
        if document is None:
            raise SearchServiceError(404, 'NOT_FOUND', 'Search document was not found')
        try:
            assert_tenant_access(document.tenant_id, tenant_id)
        except PermissionError as exc:
            raise SearchServiceError(403, 'TENANT_SCOPE_VIOLATION', 'Tenant scope does not permit this search access') from exc
        return document.to_dict()
