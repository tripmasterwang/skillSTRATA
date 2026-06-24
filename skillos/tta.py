"""Test-time skill synthesis — the "lego-style" on-the-fly adaptation.

When a new task highly overlaps a past task but is not identical, routing over the deployed
capability graph can miss a sub-capability that was never consolidated into its own skill. This
module drills from the routed skills down into the **trace layer**'s co-occurrence evidence and
*reassembles* that missing capability into an ephemeral skill, injected into the route for this
task only (used and discarded). This is what makes the trace graph an active participant at test
time rather than a passive log.

Why it is a differentiator: SkillGraph-RL / Graph-of-Skills only retrieve / route *already
built* skills at inference. Here the skill is **composed at test time from raw trace evidence**,
so the system adapts to a novel task without any RL re-training — directly supporting the
"no-RL generalization" argument.

The trigger is non-oracular: it uses only the *historical* co-occurrence statistics accumulated
by ``SkillGraph.record_trace`` plus the current seeds — never the current task's ground-truth
requirements.
"""

from __future__ import annotations

from dataclasses import dataclass

from .graph import SkillGraph


@dataclass
class Synthesized:
    atom_id: str          # the sub-capability reassembled (its stable id)
    body: str             # the skill text, taken from accumulated trace evidence
    weight: float         # co-occurrence support behind the synthesis


def synthesize_gapfill(
    graph: SkillGraph,
    seed_ids: list[str],
    deployed_ids: set[str],
    max_synth: int = 3,
    min_weight: float = 3.0,
) -> list[Synthesized]:
    """Reassemble, from trace co-occurrence, sub-capabilities that should accompany the seeds
    but have no deployed skill — the test-time gap-fill.

    Only fills genuine gaps: a candidate that already has a deployed skill is skipped (routing
    would have covered it). Returns at most ``max_synth`` ephemeral skills, highest support first.
    """
    cands = graph.trace_cooccurring(seed_ids, exclude=set(seed_ids), top_m=max_synth * 2,
                                    min_weight=min_weight)
    out: list[Synthesized] = []
    for aid, w in cands:
        if aid in deployed_ids:
            continue                       # already a real skill -> no need to synthesize
        body = graph.atom_evidence.get(aid)
        if not body:
            continue                       # no evidence to reassemble from
        out.append(Synthesized(atom_id=aid, body=body, weight=w))
        if len(out) >= max_synth:
            break
    return out
