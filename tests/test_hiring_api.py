from __future__ import annotations

import unittest

from services.hiring_service import HiringService
from services.hiring_service.api import (
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
    post_interviews,
    post_job_postings,
)


class HiringApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = HiringService()
        _, created = post_job_postings(
            self.service,
            {
                "title": "Backend Engineer",
                "department_id": "dep-eng",
                "role_id": "role-backend",
                "employment_type": "FullTime",
                "description": "Build APIs",
                "openings_count": 2,
                "posting_date": "2026-01-01",
                "status": "Open",
            },
            trace_id="trace-create",
        )
        self.posting = created["data"]

    def test_job_posting_crud_api_flow(self) -> None:
        status, fetched = get_job_posting(self.service, self.posting["job_posting_id"], trace_id="trace-get")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["data"]["title"], "Backend Engineer")
        self.assertEqual(fetched["data"]["candidate_count"], 0)

        status, updated = patch_job_posting(
            self.service,
            self.posting["job_posting_id"],
            {"status": "OnHold", "location": "Remote"},
            trace_id="trace-patch",
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["data"]["status"], "OnHold")
        self.assertEqual(updated["data"]["location"], "Remote")

        status, listing = get_job_postings(self.service, {"limit": "10", "status": "OnHold"}, trace_id="trace-list")
        self.assertEqual(status, 200)
        self.assertEqual(listing["pagination"]["count"], 1)
        self.assertEqual(listing["data"][0]["job_posting_id"], self.posting["job_posting_id"])

        status, deleted = delete_job_posting(self.service, self.posting["job_posting_id"], trace_id="trace-delete")
        self.assertEqual(status, 200)
        self.assertEqual(deleted["data"]["job_posting_id"], self.posting["job_posting_id"])

        status, missing = get_job_posting(self.service, self.posting["job_posting_id"], trace_id="trace-missing")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "NOT_FOUND")
        self.assertEqual(missing["error"]["trace_id"], "trace-missing")

    def test_candidate_and_interview_api_flow(self) -> None:
        status, created_candidate = post_candidates(
            self.service,
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Nina",
                "last_name": "Shaw",
                "email": "nina@example.com",
                "application_date": "2026-01-03",
            },
            trace_id="trace-candidate-create",
        )
        self.assertEqual(status, 201)
        candidate_id = created_candidate["data"]["candidate_id"]

        status, fetched_candidate = get_candidate(self.service, candidate_id, trace_id="trace-candidate-get")
        self.assertEqual(status, 200)
        self.assertEqual(fetched_candidate["data"]["job_posting"]["job_posting_id"], self.posting["job_posting_id"])

        status, screening = patch_candidate(
            self.service,
            candidate_id,
            {"status": "Screening", "stage_reason": "resume matched"},
            trace_id="trace-candidate-screening",
        )
        self.assertEqual(status, 200)
        self.assertEqual(screening["data"]["status"], "Screening")

        status, interviewing = patch_candidate(
            self.service,
            candidate_id,
            {"status": "Interviewing"},
            trace_id="trace-candidate-interviewing",
        )
        self.assertEqual(status, 200)
        self.assertEqual(interviewing["data"]["status"], "Interviewing")

        status, candidate_list = get_candidates(
            self.service,
            {"job_posting_id": self.posting["job_posting_id"], "status": "Interviewing"},
            trace_id="trace-candidate-list",
        )
        self.assertEqual(status, 200)
        self.assertEqual(candidate_list["pagination"]["count"], 1)
        self.assertEqual(candidate_list["data"][0]["candidate_id"], candidate_id)

        status, pipeline = get_candidate_pipeline(
            self.service,
            {"job_posting_id": self.posting["job_posting_id"], "pipeline_stage": "Interviewing"},
            trace_id="trace-pipeline",
        )
        self.assertEqual(status, 200)
        self.assertEqual(pipeline["count"], 1)
        self.assertEqual(pipeline["data"][0]["candidate_id"], candidate_id)

        status, created_interview = post_interviews(
            self.service,
            {
                "candidate_id": candidate_id,
                "interview_type": "Technical",
                "scheduled_start": "2026-01-08T10:00:00Z",
                "scheduled_end": "2026-01-08T11:00:00Z",
                "interviewer_employee_ids": ["emp-1"],
            },
            trace_id="trace-interview-create",
        )
        self.assertEqual(status, 201)
        interview_id = created_interview["data"]["interview_id"]

        status, fetched_interview = get_interview(self.service, interview_id, trace_id="trace-interview-get")
        self.assertEqual(status, 200)
        self.assertEqual(fetched_interview["data"]["candidate"]["candidate_id"], candidate_id)

        status, completed = patch_interview(
            self.service,
            interview_id,
            {"status": "Completed", "recommendation": "Hire"},
            trace_id="trace-interview-patch",
        )
        self.assertEqual(status, 200)
        self.assertEqual(completed["data"]["status"], "Completed")

        status, interview_list = get_interviews(self.service, {"candidate_id": candidate_id}, trace_id="trace-interview-list")
        self.assertEqual(status, 200)
        self.assertEqual(interview_list["pagination"]["count"], 1)
        self.assertEqual(interview_list["data"][0]["interview_id"], interview_id)

    def test_api_reports_validation_and_conflict_errors(self) -> None:
        status, invalid = get_job_postings(self.service, {"limit": "abc"}, trace_id="trace-invalid-limit")
        self.assertEqual(status, 422)
        self.assertEqual(invalid["error"]["trace_id"], "trace-invalid-limit")

        self.service.create_candidate(
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Nina",
                "last_name": "Shaw",
                "email": "nina@example.com",
                "application_date": "2026-01-03",
            }
        )
        status, conflict = delete_job_posting(self.service, self.posting["job_posting_id"], trace_id="trace-conflict")
        self.assertEqual(status, 409)
        self.assertEqual(conflict["error"]["code"], "CONFLICT")
        self.assertEqual(conflict["error"]["trace_id"], "trace-conflict")

        status, missing_candidate = post_candidates(
            self.service,
            {
                "job_posting_id": "missing-job",
                "first_name": "Bad",
                "last_name": "Reference",
                "email": "bad@example.com",
                "application_date": "2026-01-03",
            },
            trace_id="trace-missing-candidate-job",
        )
        self.assertEqual(status, 404)
        self.assertEqual(missing_candidate["error"]["code"], "NOT_FOUND")

        status, invalid_interview = post_interviews(
            self.service,
            {
                "candidate_id": "missing-candidate",
                "interview_type": "Technical",
                "scheduled_start": "2026-01-08T10:00:00Z",
                "scheduled_end": "2026-01-08T11:00:00Z",
            },
            trace_id="trace-missing-interview-candidate",
        )
        self.assertEqual(status, 404)
        self.assertEqual(invalid_interview["error"]["code"], "NOT_FOUND")

    def test_candidate_hire_api_creates_employee_profile(self) -> None:
        status, created_candidate = post_candidates(
            self.service,
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Mia",
                "last_name": "Hart",
                "email": "mia@example.com",
                "application_date": "2026-01-03",
            },
            trace_id="trace-candidate-create-hire",
        )
        self.assertEqual(status, 201)
        candidate_id = created_candidate["data"]["candidate_id"]
        patch_candidate(self.service, candidate_id, {"status": "Screening"}, trace_id="trace-screen")
        patch_candidate(self.service, candidate_id, {"status": "Interviewing"}, trace_id="trace-interview")
        patch_candidate(self.service, candidate_id, {"status": "Offered"}, trace_id="trace-offer")

        status, hired = post_candidate_hire(self.service, candidate_id, {"employee_id": "emp-300"}, trace_id="trace-hire")
        self.assertEqual(status, 200)
        self.assertEqual(hired["data"]["employee_profile"]["employee_id"], "emp-300")
        self.assertEqual(hired["data"]["status"], "Hired")


if __name__ == "__main__":
    unittest.main()
