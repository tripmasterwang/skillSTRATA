"""Curate from navigator traces — node-level attribution + off-graph → new nodes.

When the executor walks the graph through the SkillStrata navigator (skillstrata_nav MCP server) it
emits a nav-log (JSONL): which node it located/stepped onto, and where it went off-graph. That is a
*node-level* trajectory, so curate can do two things the old route-set attribution could not:

  1. **Per-node attribution** — credit/blame only the nodes the agent ACTUALLY visited (located /
     step_to'd onto), not every routed node. This is the honest heat signal that
     ``skillos.verify.mint_checkpoints_from_traces`` then reads to guard error-prone nodes.
  2. **Off-graph → new candidate skills** — every ``go_off_graph`` segment is a place the graph had
     no fit and the agent improvised; distilling it into a Fragment and INSERTing it (then letting
     the validation gate decide) is how the graph grows toward generalization. This closes the loop
     between "the agent explored outside the graph" and "the graph learned a new skill".

``distill_fn`` is injected so the graph logic stays offline-testable; the server driver supplies the
LLM-backed implementation (note → Fragment, ideally reading the off-graph transcript segment too).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .curate import Fragment
from .graph import SkillGraph
from .schema import EdgeType, TraceNode


@dataclass
class NavTrace:
    """A parsed navigator nav-log for one task run."""
    task: str = ""
    visited: list[str] = field(default_factory=list)        # node ids in step order (locate + step_to)
    offgraph: list[str] = field(default_factory=list)       # the note for each go_off_graph
    instance_id: str = ""

    @property
    def unique_visited(self) -> list[str]:
        seen, out = set(), []
        for nid in self.visited:
            if nid and nid not in seen:
                seen.add(nid); out.append(nid)
        return out


def parse_nav_log(path: str, instance_id: str = "") -> NavTrace:
    """Read a navigator nav-log (JSONL). visited = cursors of locate/step_to; offgraph = the notes."""
    tr = NavTrace(instance_id=instance_id)
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return tr
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            act = rec.get("action")
            if act == "locate":
                tr.task = tr.task or rec.get("task", "")
                if rec.get("cursor"):
                    tr.visited.append(rec["cursor"])
            elif act == "step_to":
                if rec.get("cursor"):
                    tr.visited.append(rec["cursor"])
            elif act == "go_off_graph":
                tr.offgraph.append(rec.get("note", ""))
    return tr


# --------------------------------------------------------------------------- node-level attribution
def attribute_nav_heat(graph: SkillGraph, nav: NavTrace, success: bool, *, record_trace: bool = True) -> list[str]:
    """Credit/blame ONLY the nodes the agent actually visited. Bumps per-node heat (the signal
    ``mint_checkpoints_from_traces`` reads) and, by default, writes a trace record + FIXED_BY /
    CAUSED_FAILURE edge so the trace layer reflects the real path. Returns the attributed node ids."""
    hit = [nid for nid in nav.unique_visited if nid in graph.nodes]
    for nid in hit:
        node = graph.nodes[nid]
        if success:
            node.heat.success_count += 1
        else:
            node.heat.failure_count += 1
        node.heat.last_used_step = graph.step
        if record_trace:
            tid = f"trace_{len(graph.traces)}"
            graph.traces[tid] = TraceNode(id=tid, task_id=nav.instance_id, task_type="",
                                          success=success, used_skills=[nid])
            graph.trace.add_node(tid, kind="trace", success=success)
            graph.link(nid, tid, EdgeType.FIXED_BY if success else EdgeType.CAUSED_FAILURE)
    return hit


# --------------------------------------------------------------------------- off-graph -> new nodes
def offgraph_to_fragments(nav: NavTrace, distill_fn) -> list[Fragment]:
    """Turn each off-graph segment into a candidate Fragment via the injected distiller.

    ``distill_fn(note: str, task: str) -> Fragment | None`` authors a reusable skill from the agent's
    stated reason for leaving the graph (the server driver may also feed it the off-graph transcript
    segment). Empty / None results are dropped. The returned Fragments are fed to
    ``skillos.curate.integrate_fragments`` (INSERT as CANDIDATE; the validation gate decides survival).
    """
    out = []
    for note in nav.offgraph:
        if not note.strip():
            continue
        try:
            frag = distill_fn(note, nav.task)
        except Exception:
            frag = None
        if frag is not None and frag.body.strip():
            if nav.instance_id and nav.instance_id not in frag.evidence_traces:
                frag.evidence_traces.append(nav.instance_id)
            out.append(frag)
    return out


# --------------------------------------------------------------------------- batch convenience
def curate_from_navlogs(graph: SkillGraph, runs, distill_fn=None, *, integrate=None) -> dict:
    """Fold a batch of navigator runs into the graph.

    ``runs`` = iterable of ``(navlog_path, instance_id, success)``. Does per-node heat attribution for
    every run, and (if ``distill_fn`` given) distills off-graph segments into Fragments and INSERTs
    them via ``integrate`` (default ``skillos.curate.integrate_fragments``). Returns a small summary.
    """
    if integrate is None:
        from .curate import integrate_fragments as integrate
    attributed, frags = [], []
    for path, iid, success in runs:
        nav = parse_nav_log(path, instance_id=str(iid))
        attributed += attribute_nav_heat(graph, nav, bool(success))
        if distill_fn is not None:
            frags += offgraph_to_fragments(nav, distill_fn)
    inserted = integrate(graph, frags)["inserted"] if frags else []
    return {"attributed_nodes": len(set(attributed)), "offgraph_fragments": len(frags),
            "inserted": len(inserted)}
