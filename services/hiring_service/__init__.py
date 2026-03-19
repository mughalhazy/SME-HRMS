"""Hiring service domain implementation."""

from .service import HiringService
from .api import (
    delete_job_posting,
    get_candidate,
    get_candidate_pipeline,
    get_candidates,
    get_interview,
    get_interviews,
    get_job_posting,
    get_job_postings,
    patch_candidate,
    patch_interview,
    patch_job_posting,
    post_candidates,
    post_candidate_hire,
    post_candidates_import_linkedin,
    post_interviews,
    post_interviews_google_calendar,
    post_job_postings,
)

__all__ = [
    "HiringService",
    "post_job_postings",
    "get_job_posting",
    "get_job_postings",
    "patch_job_posting",
    "delete_job_posting",
    "post_candidates",
    "post_candidate_hire",
    "post_candidates_import_linkedin",
    "get_candidate",
    "get_candidates",
    "patch_candidate",
    "get_candidate_pipeline",
    "post_interviews",
    "post_interviews_google_calendar",
    "get_interview",
    "get_interviews",
    "patch_interview",
]
