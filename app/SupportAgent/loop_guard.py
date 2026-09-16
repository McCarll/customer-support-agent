"""Stop repeated identical tool failures (LLM loop)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LoopGuard:
    max_identical_failures: int = 2
    _recent: list[str] = field(default_factory=list)
    stopped: bool = False
    reason: str = ""

    def record_failure(self, tool_name: str, error: str) -> bool:
        key = f"{tool_name}:{error}"
        if self._recent and self._recent[-1] == key:
            self._recent.append(key)
        else:
            self._recent = [key]
        if len(self._recent) >= self.max_identical_failures:
            self.stopped = True
            self.reason = (
                f"stopped after {self.max_identical_failures} identical "
                f"{tool_name} failures ({error})"
            )
            return True
        return False

    def record_success(self) -> None:
        self._recent = []
