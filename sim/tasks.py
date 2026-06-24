"""Synthetic world: a ground-truth skill universe + heterogeneous task stream.

The world is deterministic given a seed. It defines:
  * ``Atomic`` skills (the true reusable units), each serving one *domain* and carrying a body.
  * ``TaskType``s, each requiring a small set of atomics (its dependency closure) plus a set of
    *anti-skills*: atomics whose "local rules" actively mislead this task-type if loaded
    (the negative-transfer hazard from proposal §Problem 2).
  * A ``Task`` stream mixing in-distribution and OOD task-types (proposal §Benchmarks: OOD).

This lets the executor define success, token cost and negative transfer precisely, instead of
hand-waving them. Domains loosely mirror the proposal's running examples (table QA, data
analysis, web/tool-use).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


DOMAINS = ["table_qa", "data_analysis", "web_tool", "code_exec"]


@dataclass
class Atomic:
    id: str
    domain: str
    body: str
    tokens: int
    keywords: list[str] = field(default_factory=list)  # signal a task can hint at


@dataclass
class TaskType:
    name: str
    domain: str
    required: list[str]               # atomic ids that must be loaded to succeed
    anti: list[str] = field(default_factory=list)  # atomics that hurt if loaded (neg transfer)
    ood: bool = False


@dataclass
class Task:
    id: str
    task_type: str
    text: str


@dataclass
class World:
    atomics: dict[str, Atomic]
    task_types: dict[str, TaskType]
    tasks: list[Task]
    deps: dict[str, list[str]]          # atomic_id -> prerequisite atomic_ids (a DAG)
    poison: set = field(default_factory=set)   # ids of harmful/over-generalized skills (runtime)

    def atomics_in(self, domain: str) -> list[Atomic]:
        return [a for a in self.atomics.values() if a.domain == domain]

    def closure(self, atomic_ids: list[str]) -> set[str]:
        """Transitive dependency closure — the atomics actually needed to execute a task."""
        need: set[str] = set()
        stack = list(atomic_ids)
        while stack:
            a = stack.pop()
            if a in need:
                continue
            need.add(a)
            stack.extend(self.deps.get(a, []))
        return need


_VERB = ["compute", "extract", "normalize", "join", "filter", "aggregate", "validate",
         "plot", "rank", "summarize", "parse", "convert"]
_OBJ = ["the date column", "monthly totals", "the schema", "duplicate rows", "the API response",
        "nested json", "the pivot table", "currency values", "the regex match", "the time series"]


def build_world(
    seed: int = 0,
    n_atomics_per_domain: int = 12,
    n_task_types: int = 24,
    n_tasks: int = 400,
    ood_fraction: float = 0.25,
    monolith_body_tokens: int = 90,
) -> World:
    rng = random.Random(seed)

    # 1) atomic skill universe. Each atomic owns a few unique keyword tokens; its body repeats
    #    them so BM25/embedding retrieval has *real* signal (a task that needs the atomic can
    #    hint at those keywords), not random noise.
    atomics: dict[str, Atomic] = {}
    for d in DOMAINS:
        for i in range(n_atomics_per_domain):
            aid = f"{d}_a{i}"
            kws = [f"{aid}_kw{j}" for j in range(3)]
            body_len = rng.randint(40, monolith_body_tokens)
            filler = " ".join(f"{rng.choice(_VERB)} {rng.choice(_OBJ)}." for _ in range(body_len // 6))
            body = f"## {aid}\nKeywords: {' '.join(kws)}.\n{filler} " + " ".join(kws * 2)
            atomics[aid] = Atomic(id=aid, domain=d, body=body, tokens=body_len, keywords=kws)

    # 1b) atomic dependency DAG (within domain): atomic a_i may require earlier prerequisites.
    #     A task hints only at its *entry* skills; their prerequisites are NOT hinted, so only a
    #     dependency-aware router can recover them — this is the crux of the routing claim.
    deps: dict[str, list[str]] = {}
    for d in DOMAINS:
        ids = [f"{d}_a{i}" for i in range(n_atomics_per_domain)]
        for i, aid in enumerate(ids):
            if i >= 2 and rng.random() < 0.6:
                deps[aid] = rng.sample(ids[:i], rng.randint(1, 2))
            else:
                deps[aid] = []

    # 2) task types: each requires 2-4 atomics from its domain; anti = a few atomics whose
    #    rules clash (some from same domain, some cross-domain to model spurious local rules).
    #    OOD task-types preferentially *recombine* atomics already seen in in-distribution
    #    task-types — this is what makes modular skills transfer: a system that keeps atomics
    #    separate can recompose them for novel tasks, a monolith cannot.
    n_id_types = int(n_task_types * (1 - ood_fraction))
    task_types: dict[str, TaskType] = {}
    id_required_seen: list[str] = []
    for t in range(n_task_types):
        d = DOMAINS[t % len(DOMAINS)]
        pool = [a.id for a in atomics.values() if a.domain == d]
        is_ood = t >= n_id_types
        if is_ood:
            reused = [a for a in id_required_seen if atomics[a].domain == d]
            k = rng.randint(2, 4)
            required = rng.sample(reused, min(k, len(reused))) if reused else []
            if len(required) < k:
                required += rng.sample([a for a in pool if a not in required], k - len(required))
        else:
            required = rng.sample(pool, rng.randint(2, 4))
            id_required_seen.extend(required)
        anti_pool = [a for a in pool if a not in required]
        cross = [a.id for a in atomics.values() if a.domain != d]
        anti = rng.sample(anti_pool, min(2, len(anti_pool))) + rng.sample(cross, 2)
        task_types[f"tt_{t}"] = TaskType(
            name=f"tt_{t}", domain=d, required=required, anti=anti, ood=is_ood
        )

    # 3) task stream. In-distribution task-types appear early & often; OOD types appear late
    #    (the "heterogeneous task stream" / OOD transfer setting).
    id_types = [k for k, v in task_types.items() if not v.ood]
    ood_types = [k for k, v in task_types.items() if v.ood]
    tasks: list[Task] = []
    for i in range(n_tasks):
        progress = i / n_tasks
        if progress > 0.6 and ood_types and rng.random() < 0.5:
            tt = rng.choice(ood_types)
        else:
            tt = rng.choice(id_types or ood_types)
        ttype = task_types[tt]
        # the task hints at SOME (noisy subset) of its required atomics' keywords — a real task
        # description rarely names every needed skill, so retrieval must recover the rest.
        hinted = []
        for aid in ttype.required:
            if rng.random() < 0.6:                       # 60% of required skills are hinted
                hinted.append(rng.choice(atomics[aid].keywords))
        filler = " ".join(f"{rng.choice(_VERB)} {rng.choice(_OBJ)}" for _ in range(rng.randint(3, 6)))
        text = f"[{ttype.domain}] {filler} " + " ".join(hinted)
        tasks.append(Task(id=f"task_{i}", task_type=tt, text=text))

    return World(atomics=atomics, task_types=task_types, tasks=tasks, deps=deps)
