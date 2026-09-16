"""Local Cedar approximation used by the FastMCP Gateway.

Production uses AgentCore Policy in ENFORCE mode. This evaluator reads the
same Cedar files so local tests exercise the same refund limit. It is not a
full Cedar engine: it understands permit/forbid, named actions, and
context.input.amount comparisons.

Set AGENTCORE_POLICY_ENFORCE=1 to skip local evaluation when AWS Policy is
already attached to the Gateway.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Effect = Literal["permit", "forbid"]
Decision = Literal["ALLOW", "DENY"]

POLICY_DIR = Path(__file__).resolve().parents[1] / "policy"

_POLICY_BLOCK = re.compile(
    r"(permit|forbid)\s*\((.*?)\)\s*(when\s*\{(.*?)\})?\s*;",
    re.DOTALL | re.IGNORECASE,
)
_ACTION = re.compile(r'action\s*==\s*AgentCore::Action::"([^"]+)"')
_COMPARE = re.compile(
    r"context\.input\.amount\s*(<=|>=|<|>|==)\s*([0-9]+(?:\.[0-9]+)?)"
)
_HAS_AMOUNT = re.compile(r"context\.input\s+has\s+amount")


@dataclass(frozen=True)
class PolicyRule:
    effect: Effect
    actions: tuple[str, ...]
    when_block: str
    source: str


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    matched_rule: str | None
    reason: str
    tool_name: str
    arguments: dict[str, Any]


def short_action_name(action: str) -> str:
    if "___" in action:
        return action.split("___", 1)[1]
    return action


def _amount(arguments: dict[str, Any]) -> float | None:
    value = arguments.get("amount")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def condition_matches(when_block: str, arguments: dict[str, Any]) -> bool:
    if not when_block.strip():
        return True
    block = " ".join(when_block.split())
    amount = _amount(arguments)
    if _HAS_AMOUNT.search(block) and amount is None:
        return False
    compare = _COMPARE.search(block)
    if not compare:
        return True
    if amount is None:
        return False
    operator, raw_limit = compare.group(1), float(compare.group(2))
    if operator == "<=":
        return amount <= raw_limit
    if operator == "<":
        return amount < raw_limit
    if operator == ">=":
        return amount >= raw_limit
    if operator == ">":
        return amount > raw_limit
    return amount == raw_limit


def load_policies(policy_dir: Path | None = None) -> list[PolicyRule]:
    directory = policy_dir or POLICY_DIR
    rules: list[PolicyRule] = []
    for path in sorted(directory.glob("*.cedar")):
        text = path.read_text(encoding="utf-8")
        for match in _POLICY_BLOCK.finditer(text):
            actions = tuple(
                sorted({short_action_name(action) for action in _ACTION.findall(match.group(2))})
            )
            if not actions:
                actions = ("*",)
            rules.append(
                PolicyRule(
                    effect=match.group(1).lower(),  # type: ignore[arg-type]
                    actions=actions,
                    when_block=(match.group(4) or "").strip(),
                    source=path.name,
                )
            )
    return rules


def evaluate(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    policy_dir: Path | None = None,
) -> PolicyDecision:
    """Default-deny, forbid-wins — the same semantics as AgentCore Policy."""
    if os.getenv("AGENTCORE_POLICY_ENFORCE") == "1":
        return PolicyDecision(
            decision="ALLOW",
            matched_rule=None,
            reason="Local evaluator skipped; AgentCore Policy ENFORCE is attached.",
            tool_name=short_action_name(tool_name),
            arguments=arguments,
        )
    tool = short_action_name(tool_name)
    matching_forbid: PolicyRule | None = None
    matching_permit: PolicyRule | None = None
    for rule in load_policies(policy_dir):
        if "*" not in rule.actions and tool not in rule.actions:
            continue
        if not condition_matches(rule.when_block, arguments):
            continue
        if rule.effect == "forbid" and matching_forbid is None:
            matching_forbid = rule
        elif rule.effect == "permit" and matching_permit is None:
            matching_permit = rule

    if matching_forbid is not None:
        return PolicyDecision(
            decision="DENY",
            matched_rule=matching_forbid.source,
            reason="Cedar forbid matched (forbid-wins).",
            tool_name=tool,
            arguments=arguments,
        )
    if matching_permit is not None:
        return PolicyDecision(
            decision="ALLOW",
            matched_rule=matching_permit.source,
            reason="Cedar permit matched and no forbid applied.",
            tool_name=tool,
            arguments=arguments,
        )
    return PolicyDecision(
        decision="DENY",
        matched_rule=None,
        reason="Default deny: no Cedar permit matched this tool call.",
        tool_name=tool,
        arguments=arguments,
    )
