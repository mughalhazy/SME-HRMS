from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable


SECTION_HEADERS = ("skills", "experience", "education")


@dataclass(slots=True)
class CandidateProfile:
    name: str
    skills: list[str]
    experience: list[str]
    education: list[str]


@dataclass(slots=True)
class CandidateScore:
    candidate_name: str
    score: float
    explanation: str
    matched_skills: list[str]
    experience_years: float


@dataclass(slots=True)
class OnboardingTask:
    task: str
    assignee: str
    stage: str


class InterviewWorkflow:
    """Deterministic interview stage progression."""

    def __init__(self, stages: list[str] | None = None) -> None:
        self.stages = stages or ["Applied", "Screening", "Interview", "Offer", "Hired"]
        self._positions = {stage: idx for idx, stage in enumerate(self.stages)}
        self._candidate_stages: dict[str, str] = {}

    def define_candidate(self, candidate_id: str, initial_stage: str | None = None) -> str:
        stage = initial_stage or self.stages[0]
        if stage not in self._positions:
            raise ValueError(f"Unknown stage: {stage}")
        self._candidate_stages[candidate_id] = stage
        return stage

    def move_candidate(self, candidate_id: str, target_stage: str) -> str:
        if target_stage not in self._positions:
            raise ValueError(f"Unknown stage: {target_stage}")
        if candidate_id not in self._candidate_stages:
            self.define_candidate(candidate_id)

        current_stage = self._candidate_stages[candidate_id]
        if self._positions[target_stage] < self._positions[current_stage]:
            raise ValueError("Cannot move candidate backwards in workflow")

        self._candidate_stages[candidate_id] = target_stage
        return target_stage

    def current_stage(self, candidate_id: str) -> str:
        return self._candidate_stages[candidate_id]


def parse_cv(cv_input: str | bytes | Path) -> CandidateProfile:
    """Parse CV content from text or PDF-ish payload into a structured profile."""

    text = _read_cv_content(cv_input)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("CV content is empty")

    name = _extract_name(lines)
    sections = _extract_sections(lines)

    return CandidateProfile(
        name=name,
        skills=_split_list_items(sections.get("skills", [])),
        experience=sections.get("experience", []),
        education=sections.get("education", []),
    )


def score_candidate(
    candidate: CandidateProfile,
    required_skills: Iterable[str],
    minimum_years_experience: float,
) -> CandidateScore:
    required = [skill.strip().lower() for skill in required_skills if skill.strip()]
    candidate_skill_map = {skill.lower(): skill for skill in candidate.skills}
    matched = [candidate_skill_map[s] for s in required if s in candidate_skill_map]

    skills_score = (len(matched) / len(required) * 100.0) if required else 100.0
    years = _extract_experience_years(candidate.experience)
    experience_score = 100.0 if minimum_years_experience <= 0 else min(years / minimum_years_experience, 1.0) * 100.0

    total = round((skills_score * 0.7) + (experience_score * 0.3), 2)
    explanation = (
        f"skills_match={len(matched)}/{len(required) or 0} ({skills_score:.2f}), "
        f"experience_years={years:.1f}/{minimum_years_experience:.1f} ({experience_score:.2f}), "
        f"weighted_score=0.7*skills+0.3*experience={total:.2f}"
    )

    return CandidateScore(
        candidate_name=candidate.name,
        score=total,
        explanation=explanation,
        matched_skills=matched,
        experience_years=years,
    )


def rank_candidates(candidates: Iterable[CandidateScore]) -> list[CandidateScore]:
    return sorted(candidates, key=lambda c: (-c.score, c.candidate_name.lower()))


def generate_onboarding_checklist(candidate_name: str, assignees: list[str]) -> list[OnboardingTask]:
    if not assignees:
        raise ValueError("At least one assignee is required")

    tasks = [
        ("Preboarding", f"Prepare welcome packet for {candidate_name}"),
        ("Day1", "Provision email and HRMS access"),
        ("Day1", "Set up payroll and benefits enrollment"),
        ("Week1", "Schedule manager onboarding sync"),
        ("Week1", "Complete policy and compliance training"),
    ]
    checklist: list[OnboardingTask] = []
    for idx, (stage, task) in enumerate(tasks):
        checklist.append(OnboardingTask(task=task, assignee=assignees[idx % len(assignees)], stage=stage))
    return checklist


def _read_cv_content(cv_input: str | bytes | Path) -> str:
    if isinstance(cv_input, Path):
        content = cv_input.read_bytes()
        return _decode_pdf_or_text(content)

    if isinstance(cv_input, bytes):
        return _decode_pdf_or_text(cv_input)

    path = Path(cv_input)
    if path.exists() and path.is_file():
        return _decode_pdf_or_text(path.read_bytes())
    return cv_input


def _decode_pdf_or_text(content: bytes) -> str:
    if content.startswith(b"%PDF"):
        decoded = content.decode("latin-1", errors="ignore")
        tokens = re.findall(r"\(([^()]*)\)\s*Tj", decoded)
        if tokens:
            return "\n".join(token.replace("\\n", " ") for token in tokens)
    return content.decode("utf-8", errors="ignore")


def _extract_name(lines: list[str]) -> str:
    for line in lines:
        if ":" in line and line.lower().startswith("name"):
            return line.split(":", 1)[1].strip()
    return lines[0]


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"skills": [], "experience": [], "education": []}
    current: str | None = None
    for line in lines:
        normalized = line.strip().lower().rstrip(":")
        if normalized in SECTION_HEADERS:
            current = normalized
            continue

        if line.lower().startswith("name:"):
            continue

        if current:
            sections[current].append(line)

    return sections


def _split_list_items(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        for part in re.split(r"[,|•]", item):
            cleaned = part.strip(" -\t")
            if cleaned:
                result.append(cleaned)
    return result


def _extract_experience_years(experience_lines: list[str]) -> float:
    years = 0.0
    for line in experience_lines:
        for match in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs|year|yr)", line.lower()):
            years += float(match)
    return years
