"""Self-evolution loop primitive — distill skills from trace evidence and consolidate them.

This closes the self-evolution loop with **no RL, no gradients**. Test-time LEGO assembly
(``skillos.tta``) is ephemeral, but the trace evidence it draws on **accumulates** in
``SkillGraph.cooc`` / ``atom_evidence``. At the end of each curate round we distill the
sub-capabilities that have repeatedly co-occurred in *successful* runs and **consolidate** them
into deployed skills. Next round, ASSEMBLE routes them directly instead of re-synthesizing — so
the system gets stronger over rounds.

Why this counts as verification without RL: ``record_trace`` weights successful co-occurrence
more than failed (``w_success > w_fail``), so a high accumulated weight is an implicit
propose-then-verify signal ("this capability has helped before, repeatedly").
"""

from __future__ import annotations

from .graph import SkillGraph
from .operations import insert
from .schema import Granularity, GovernanceNode, SkillNode, Status, slugify


def distill_and_consolidate(
    graph: SkillGraph, min_weight: float = 4.0, max_new: int = 4,
) -> list[str]:
    """Round-end curate step: fix sub-capabilities that proved useful in traces but have no
    deployed skill, turning them into deployed skills in the Skill Strata.

    Returns the ids consolidated this round (drives the "synthesis ↓ as library grows" curve).
    """
    deployed = {n.id for n in graph.deployed()}
    # success-weighted total co-occurrence support per sub-capability
    score: dict[str, float] = {}
    for (a, b), w in graph.cooc.items():
        for x in (a, b):
            score[x] = score.get(x, 0.0) + w
    cands = sorted(
        [(x, s) for x, s in score.items()
         if x not in deployed and s >= min_weight and x in graph.atom_evidence],
        key=lambda t: -t[1],
    )[:max_new]

    consolidated: list[str] = []
    for aid, s in cands:
        body = graph.atom_evidence[aid]
        if aid in graph.nodes:
            node = graph.nodes[aid]
            node.status = Status.DEPLOYED        # re-discover a previously un-fixed capability
            if not node.body:
                node.body = body
        else:
            insert(graph, SkillNode.make(id=aid, name=aid, description=aid, body=body,
                                         granularity=Granularity.ATOMIC, status=Status.DEPLOYED))
            graph.nodes[aid].status = Status.DEPLOYED
        graph.nodes[aid].heat.token_cost = max(1, len(body) // 4)
        graph.add_rule(GovernanceNode(
            id=slugify(f"consolidate_{aid}_{graph.step}"), kind="consolidation",
            statement=f"consolidate {aid} from trace evidence (support {s:.1f})", targets=[aid]))
        consolidated.append(aid)
    return consolidated
