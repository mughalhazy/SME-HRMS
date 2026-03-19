from __future__ import annotations

import unittest

from services.hiring_service import HiringService
from services.hiring_service.api import delete_job_posting, get_job_posting, get_job_postings, patch_job_posting, post_job_postings


class HiringJobPostingApiTests(unittest.TestCase):
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
        self.assertEqual(missing["error"]["traceId"], "trace-missing")

    def test_job_posting_api_reports_validation_and_conflict_errors(self) -> None:
        status, invalid = get_job_postings(self.service, {"limit": "abc"}, trace_id="trace-invalid-limit")
        self.assertEqual(status, 422)
        self.assertEqual(invalid["error"]["traceId"], "trace-invalid-limit")

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
        self.assertEqual(conflict["error"]["traceId"], "trace-conflict")


if __name__ == "__main__":
    unittest.main()
