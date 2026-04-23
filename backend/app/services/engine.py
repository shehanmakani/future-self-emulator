from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FuturePersona:
    name: str
    bias: str
    weight: float


PERSONAS = (
    FuturePersona("Disciplined Future You", "deadline_first", 1.0),
    FuturePersona("Opportunistic Future You", "impact_first", 0.85),
    FuturePersona("Protective Future You", "risk_first", 0.75),
)


def _normalize_tasks(context: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    for index, item in enumerate(context.get("candidate_tasks", []), start=1):
        if not isinstance(item, dict):
            continue
        tasks.append(
            {
                "id": item.get("id", f"task-{index}"),
                "title": item.get("title", f"Untitled task {index}"),
                "description": item.get("description", ""),
                "source": item.get("source", "unknown"),
                "urgency": float(item.get("urgency", 0.5)),
                "impact": float(item.get("impact", 0.5)),
                "effort": float(item.get("effort", 0.5)),
                "risk": float(item.get("risk", 0.5)),
                "deadline": item.get("deadline"),
                "execution": item.get("execution"),
            }
        )
    return tasks


def _score_task(task: dict[str, Any], persona: FuturePersona, hour: int) -> float:
    urgency = task["urgency"]
    impact = task["impact"]
    effort = task["effort"]
    risk = task["risk"]

    score = 0.0
    if persona.bias == "deadline_first":
        score += urgency * 0.45 + impact * 0.35
    elif persona.bias == "impact_first":
        score += impact * 0.50 + urgency * 0.20
    elif persona.bias == "risk_first":
        score += urgency * 0.25 + impact * 0.20 + (1 - risk) * 0.35

    score += (1 - effort) * 0.15

    # Time-of-day bias: late night is better for deep work, mornings for outreach.
    source = str(task.get("source", "")).lower()
    if 0 <= hour < 6 and source in {"repo", "code", "research"}:
        score += 0.10
    if 6 <= hour < 12 and source in {"calendar", "communication", "email"}:
        score += 0.10

    return round(score * persona.weight, 4)


def simulate_futures(decision: str, profile: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    candidate_tasks = _normalize_tasks(context)
    now = context.get("current_time") or datetime.now().isoformat()
    hour = datetime.fromisoformat(now).hour if "T" in now else datetime.now().hour

    futures = []
    for persona in PERSONAS:
        ranked = sorted(
            candidate_tasks,
            key=lambda task: _score_task(task, persona, hour),
            reverse=True,
        )
        top = ranked[:3]
        futures.append(
            {
                "persona": persona.name,
                "bias": persona.bias,
                "top_tasks": [
                    {
                        "id": task["id"],
                        "title": task["title"],
                        "score": _score_task(task, persona, hour),
                        "reason": _task_reason(task, persona),
                    }
                    for task in top
                ],
            }
        )

    return {
        "decision": decision,
        "profile": profile,
        "generated_at": now,
        "futures": futures,
    }


def recommend_next_action(profile: str, context: dict[str, Any]) -> dict[str, Any]:
    tasks = _normalize_tasks(context)
    if not tasks:
        return {
            "recommended_task": None,
            "confidence": 0.0,
            "summary": "No candidate tasks were available to rank.",
            "futures": [],
        }

    simulation = simulate_futures(
        decision="What should I do next without waiting for a prompt?",
        profile=profile,
        context=context,
    )

    aggregate: dict[str, dict[str, Any]] = {}
    for future in simulation["futures"]:
        for rank, task in enumerate(future["top_tasks"], start=1):
            entry = aggregate.setdefault(
                task["id"],
                {"title": task["title"], "votes": 0, "score_total": 0.0, "reasons": []},
            )
            entry["votes"] += max(0, 4 - rank)
            entry["score_total"] += task["score"]
            entry["reasons"].append(f"{future['persona']}: {task['reason']}")

    best_id, best = max(
        aggregate.items(),
        key=lambda item: (item[1]["votes"], item[1]["score_total"]),
    )
    selected = next(task for task in tasks if task["id"] == best_id)
    confidence = min(0.99, round((best["votes"] / 9) * 0.7 + (best["score_total"] / 3) * 0.3, 2))

    return {
        "recommended_task": selected,
        "confidence": confidence,
        "summary": (
            f"{selected['title']} ranked highest across the simulated futures "
            f"because it balances urgency, impact, and acceptable execution risk."
        ),
        "futures": simulation["futures"],
    }


def run_simulation(decision: str, profile: str) -> str:
    result = simulate_futures(decision, profile, context={})
    persona_names = ", ".join(item["persona"] for item in result["futures"])
    return f"Future simulation for {decision} with profile {profile}. Personas: {persona_names}"


def _task_reason(task: dict[str, Any], persona: FuturePersona) -> str:
    if persona.bias == "deadline_first":
        return "closest to deadline with enough upside to justify doing it now"
    if persona.bias == "impact_first":
        return "highest expected leverage across current projects"
    return "lowest-risk move that still creates forward motion"
