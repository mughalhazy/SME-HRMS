from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InsightSignal:
    signal: str
    text: str
    score: float
    evidence: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "text": self.text,
            "score": self.score,
            "evidence": dict(self.evidence),
        }


class PerformanceInsightsService:
    """Generates explainable, deterministic performance insight cards."""

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        employee = payload.get("employee", {})
        manager = payload.get("manager", {})
        skills = payload.get("skills", {})

        employee_summary = self._employee_summary(employee)
        manager_insights = self._manager_insights(manager)
        skill_signals = self._skill_signals(skills)

        overall_score = round(
            (employee_summary.score * 0.4)
            + (manager_insights.score * 0.35)
            + (skill_signals.score * 0.25),
            2,
        )

        return {
            "employee_performance_summary": employee_summary.to_dict(),
            "manager_insights": manager_insights.to_dict(),
            "skill_signals": skill_signals.to_dict(),
            "overall_score": overall_score,
        }

    def _employee_summary(self, employee: dict[str, Any]) -> InsightSignal:
        goals_attainment = self._clamp(employee.get("goals_attainment", 0))
        quality_score = self._clamp(employee.get("quality_score", 0))
        delivery_timeliness = self._clamp(employee.get("delivery_timeliness", 0))

        score = round((goals_attainment * 0.5) + (quality_score * 0.3) + (delivery_timeliness * 0.2), 2)
        text = (
            "Employee performance is stable"
            if score >= 60
            else "Employee performance needs focused support"
        )
        return InsightSignal(
            signal="employee_performance_summary",
            text=text,
            score=score,
            evidence={
                "goals_attainment": goals_attainment,
                "quality_score": quality_score,
                "delivery_timeliness": delivery_timeliness,
            },
        )

    def _manager_insights(self, manager: dict[str, Any]) -> InsightSignal:
        feedback_sentiment = self._clamp(manager.get("feedback_sentiment", 0))
        coaching_frequency = self._clamp(manager.get("coaching_frequency", 0))
        blocker_resolution = self._clamp(manager.get("blocker_resolution", 0))

        score = round((feedback_sentiment * 0.4) + (coaching_frequency * 0.3) + (blocker_resolution * 0.3), 2)
        text = (
            "Manager support is enabling growth"
            if score >= 65
            else "Manager support cadence should be improved"
        )
        return InsightSignal(
            signal="manager_insights",
            text=text,
            score=score,
            evidence={
                "feedback_sentiment": feedback_sentiment,
                "coaching_frequency": coaching_frequency,
                "blocker_resolution": blocker_resolution,
            },
        )

    def _skill_signals(self, skills: dict[str, Any]) -> InsightSignal:
        skill_coverage = self._clamp(skills.get("skill_coverage", 0))
        learning_velocity = self._clamp(skills.get("learning_velocity", 0))
        critical_skill_gap = self._clamp(skills.get("critical_skill_gap", 100))

        score = round((skill_coverage * 0.45) + (learning_velocity * 0.35) + ((100 - critical_skill_gap) * 0.2), 2)
        text = (
            "Skill signals show healthy progression"
            if score >= 60
            else "Skill risk detected in critical competencies"
        )
        return InsightSignal(
            signal="skill_signals",
            text=text,
            score=score,
            evidence={
                "skill_coverage": skill_coverage,
                "learning_velocity": learning_velocity,
                "critical_skill_gap": critical_skill_gap,
            },
        )

    @staticmethod
    def _clamp(value: Any) -> float:
        numeric = float(value)
        if numeric < 0:
            return 0.0
        if numeric > 100:
            return 100.0
        return round(numeric, 2)
