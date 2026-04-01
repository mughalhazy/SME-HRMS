from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from math import sqrt
from typing import Iterable


@dataclass(slots=True)
class FaceRecognitionAttendanceRecord:
    employee_id: str
    timestamp: datetime
    confidence: Decimal


class FaceRecognitionService:
    """Lightweight face encoding ingestion + matching for attendance capture flows."""

    def __init__(self) -> None:
        self._employee_db: dict[str, tuple[float, ...]] = {}

    @staticmethod
    def _normalize_encoding(frame: Iterable[float | int | str]) -> tuple[float, ...]:
        encoding = tuple(float(value) for value in frame)
        if not encoding:
            raise ValueError("frame encoding cannot be empty")
        return encoding

    @staticmethod
    def _distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        if len(a) != len(b):
            raise ValueError("encoding lengths must match")
        return sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))

    @staticmethod
    def _confidence(distance: float) -> Decimal:
        confidence = max(0.0, 1.0 - (distance / 2.0))
        return Decimal(str(confidence)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    def ingest_employee_encodings(self, employee_database: dict[str, Iterable[float | int | str]]) -> None:
        self._employee_db = {
            employee_id: self._normalize_encoding(encoding) for employee_id, encoding in employee_database.items()
        }

    def match_employee_identity(self, frame: Iterable[float | int | str]) -> FaceRecognitionAttendanceRecord | None:
        if not self._employee_db:
            raise ValueError("employee database is empty; ingest encodings first")

        candidate_encoding = self._normalize_encoding(frame)

        best_match_id: str | None = None
        best_distance: float | None = None

        for employee_id, known_encoding in self._employee_db.items():
            distance = self._distance(candidate_encoding, known_encoding)
            if best_distance is None or distance < best_distance:
                best_match_id = employee_id
                best_distance = distance

        if best_match_id is None or best_distance is None:
            return None

        return FaceRecognitionAttendanceRecord(
            employee_id=best_match_id,
            timestamp=datetime.utcnow(),
            confidence=self._confidence(best_distance),
        )
