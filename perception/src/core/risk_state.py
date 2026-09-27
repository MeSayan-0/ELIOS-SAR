from dataclasses import dataclass
import time


@dataclass
class PersistentRisk:
    level: str = "LOW"
    score: int = 0
    reasons: list[str] | None = None
    last_update: float = 0.0

RiskState = PersistentRisk


class PersistentRiskState:
    LEVEL_ORDER = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
        "CRITICAL": 3,
    }

    def __init__(
        self,
        persistence_seconds: float = 1.0,
        decay_seconds: float = 5.0,
        **kwargs
    ):
        self.persistence_seconds = persistence_seconds
        self.decay_seconds = decay_seconds

        self.current = PersistentRisk(
            reasons=[]
        )

        self.pending_level = None
        self.pending_since = None

    def update(
        self,
        candidate_level: str,
        candidate_score: int = 0,
        reasons=None
    ) -> PersistentRisk:

        candidate_level = str(
            candidate_level or "LOW"
        ).upper()

        if candidate_level == "MODERATE":
            candidate_level = "MEDIUM"

        if candidate_level not in self.LEVEL_ORDER:
            candidate_level = "LOW"

        now = time.monotonic()

        current_rank = self.LEVEL_ORDER.get(
            self.current.level,
            0
        )

        candidate_rank = self.LEVEL_ORDER[
            candidate_level
        ]

        # Immediate escalation for more dangerous states
        if candidate_rank > current_rank:
            self.current = PersistentRisk(
                level=candidate_level,
                score=int(candidate_score),
                reasons=list(reasons or []),
                last_update=now
            )

            self.pending_level = None
            self.pending_since = None

            return self.current

        # Same-level update
        if candidate_level == self.current.level:
            self.current.score = int(
                candidate_score
            )
            self.current.reasons = list(
                reasons or []
            )
            self.current.last_update = now

            self.pending_level = None
            self.pending_since = None

            return self.current

        # Lower-risk candidate: require decay period
        if self.pending_level != candidate_level:
            self.pending_level = candidate_level
            self.pending_since = now
        else:
            elapsed = now - (
                self.pending_since or now
            )

            if elapsed >= self.decay_seconds:
                self.current = PersistentRisk(
                    level=candidate_level,
                    score=int(candidate_score),
                    reasons=list(reasons or []),
                    last_update=now
                )

                self.pending_level = None
                self.pending_since = None

        return self.current

    def get(self) -> PersistentRisk:
        return self.current

    def snapshot(self) -> PersistentRisk:
        return self.current
