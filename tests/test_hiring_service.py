import unittest

from services.hiring_service import HiringService
from services.hiring_service.service import HiringValidationError


class HiringServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = HiringService()
        self.posting = self.service.create_job_posting(
            {
                "title": "Backend Engineer",
                "department_id": "dep-1",
                "role_id": "role-1",
                "employment_type": "FullTime",
                "description": "Build core APIs",
                "openings_count": 2,
                "posting_date": "2026-01-01",
                "status": "Open",
            }
        )

    def test_candidate_hiring_happy_path(self) -> None:
        candidate = self.service.create_candidate(
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Ava",
                "last_name": "Stone",
                "email": "ava@example.com",
                "application_date": "2026-01-03",
            }
        )
        self.assertEqual(candidate["status"], "Applied")

        screening = self.service.update_candidate(candidate["candidate_id"], {"status": "Screening"})
        self.assertEqual(screening["status"], "Screening")

        interviewing = self.service.update_candidate(candidate["candidate_id"], {"status": "Interviewing"})
        self.assertEqual(interviewing["status"], "Interviewing")

        interview = self.service.create_interview(
            {
                "candidate_id": candidate["candidate_id"],
                "interview_type": "Technical",
                "scheduled_start": "2026-01-08T10:00:00Z",
                "scheduled_end": "2026-01-08T11:00:00Z",
                "interviewer_employee_ids": ["emp-1", "emp-2"],
            }
        )
        self.assertEqual(interview["status"], "Scheduled")

        completed = self.service.update_interview(interview["interview_id"], {"status": "Completed", "recommendation": "Hire"})
        self.assertEqual(completed["status"], "Completed")

        offered = self.service.update_candidate(candidate["candidate_id"], {"status": "Offered"})
        self.assertEqual(offered["status"], "Offered")

        hired = self.service.mark_candidate_hired(candidate["candidate_id"])
        self.assertEqual(hired["status"], "Hired")

        event_types = [event["event_type"] for event in self.service.events]
        self.assertIn("JobPostingOpened", event_types)
        self.assertIn("CandidateApplied", event_types)
        self.assertIn("InterviewScheduled", event_types)
        self.assertIn("InterviewCompleted", event_types)
        self.assertIn("CandidateHired", event_types)

    def test_invalid_candidate_transition_rejected(self) -> None:
        candidate = self.service.create_candidate(
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Kai",
                "last_name": "Ng",
                "email": "kai@example.com",
                "application_date": "2026-01-03",
            }
        )

        with self.assertRaises(HiringValidationError):
            self.service.update_candidate(candidate["candidate_id"], {"status": "Hired"})

    def test_duplicate_candidate_email_per_posting_rejected(self) -> None:
        self.service.create_candidate(
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "First",
                "last_name": "Person",
                "email": "dupe@example.com",
                "application_date": "2026-01-03",
            }
        )

        with self.assertRaises(HiringValidationError):
            self.service.create_candidate(
                {
                    "job_posting_id": self.posting["job_posting_id"],
                    "first_name": "Second",
                    "last_name": "Person",
                    "email": "dupe@example.com",
                    "application_date": "2026-01-04",
                }
            )

    def test_list_candidate_pipeline_view_maps_read_model_fields(self) -> None:
        candidate = self.service.create_candidate(
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Noah",
                "last_name": "Lane",
                "email": "noah@example.com",
                "application_date": "2026-01-03",
            }
        )
        self.service.update_candidate(candidate["candidate_id"], {"status": "Screening"})
        self.service.update_candidate(candidate["candidate_id"], {"status": "Interviewing"})
        self.service.create_interview(
            {
                "candidate_id": candidate["candidate_id"],
                "interview_type": "Technical",
                "scheduled_start": "2026-01-08T10:00:00Z",
                "scheduled_end": "2026-01-08T11:00:00Z",
                "interviewer_employee_ids": ["emp-1"],
            }
        )

        rows = self.service.list_candidate_pipeline_view(pipeline_stage="Interviewing")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["candidate_id"], candidate["candidate_id"])
        self.assertEqual(row["candidate_name"], "Noah Lane")
        self.assertEqual(row["candidate_email"], "noah@example.com")
        self.assertEqual(row["job_posting_id"], self.posting["job_posting_id"])
        self.assertEqual(row["job_title"], "Backend Engineer")
        self.assertEqual(row["department_id"], "dep-1")
        self.assertEqual(row["pipeline_stage"], "Interviewing")
        self.assertEqual(row["next_interview_at"], "2026-01-08T10:00:00+00:00")
        self.assertEqual(row["interview_count"], 1)

    def test_build_hiring_ui_returns_job_postings_and_candidate_pipeline_surfaces(self) -> None:
        candidate = self.service.create_candidate(
            {
                "job_posting_id": self.posting["job_posting_id"],
                "first_name": "Iris",
                "last_name": "Vale",
                "email": "iris@example.com",
                "application_date": "2026-01-03",
            }
        )

        surfaces = self.service.build_hiring_ui(department_id="dep-1", job_posting_id=self.posting["job_posting_id"])
        self.assertEqual(set(surfaces.keys()), {"job_postings", "candidate_pipeline"})
        self.assertEqual(len(surfaces["job_postings"]), 1)
        self.assertEqual(surfaces["job_postings"][0]["job_posting_id"], self.posting["job_posting_id"])
        self.assertEqual(len(surfaces["candidate_pipeline"]), 1)
        self.assertEqual(surfaces["candidate_pipeline"][0]["candidate_id"], candidate["candidate_id"])


if __name__ == "__main__":
    unittest.main()
