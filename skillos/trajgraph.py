"""Trajectory-chain graph (the 'draw chains, merge, select subgraph' SkillStrata variant).

This is the paradigm distinct from the distill-into-skill-nodes pipeline in
``skillos.curate``/``skillos.graph``. Here:

  1. each TRAIN trajectory is drawn by an LLM into an ordered CHAIN of *canonical
     operation-step* nodes (reusing a running node registry so equivalent steps across
     trajectories collapse to the SAME node);
  2. the chains MERGE into one directed graph (popular steps become hubs), edges =
     next-step TEMPORAL_ORDER, success-weighted;
  3. a SKILL = a task-conditioned SUBGRAPH: seed by the question, then walk the
     success-weighted edges to assemble the *consensus success path* for that kind of
     task, rendered to a SKILL.md.

Nodes are abstracted operation-steps (NOT raw tool calls, NOT distilled whole-skills).
Merge criterion = LLM canonical-label reuse (the registry), with a lexical backstop.
Self-contained: only stdlib + networkx + rank_bm25 (already a skillos dep).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict

import networkx as nx
from rank_bm25 import BM25Okapi


# --------------------------------------------------------------------------- ids
def canon_id(text: str) -> str:
    """snake_case canonical step id."""
    s = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return s[:48] or "step"


# ------------------------------------------------------------------------- nodes
@dataclass
class StepNode:
    id: str
    desc: str = ""                       # one-line "what this operation does"
    n_visit: int = 0
    n_success: int = 0
    pos_sum: float = 0.0                 # sum of (normalized) positions, for ordering
    pos_n: int = 0
    task_types: dict = field(default_factory=dict)   # difficulty/type -> count
    examples: list = field(default_factory=list)     # a few example questions

    @property
    def success_rate(self) -> float:
        return self.n_success / self.n_visit if self.n_visit else 0.0

    @property
    def avg_pos(self) -> float:
        return self.pos_sum / self.pos_n if self.pos_n else 0.5


class ChainGraph:
    """Merged directed graph of canonical operation-steps drawn from trajectory chains."""

    def __init__(self):
        self.g = nx.DiGraph()
        self.nodes: dict[str, StepNode] = {}

    # --- registry passed to the LLM so it reuses existing canonical step ids ---
    def registry_text(self, limit: int = 60) -> str:
        if not self.nodes:
            return "(empty — mint new ids)"
        ranked = sorted(self.nodes.values(), key=lambda n: -n.n_visit)[:limit]
        return "\n".join(f"- {n.id}: {n.desc}" for n in ranked)

    # --- add one drawn chain ---
    def add_chain(self, chain: list[dict], success: bool, task_type: str = "",
                  question: str = "", w_success: float = 2.0, w_fail: float = 0.5) -> None:
        """chain = ordered [{"id":canonical, "desc":...}, ...]."""
        w = w_success if success else w_fail
        L = max(1, len(chain))
        prev = None
        for i, step in enumerate(chain):
            sid = canon_id(step.get("id") or step.get("desc") or "step")
            node = self.nodes.get(sid)
            if node is None:
                node = StepNode(id=sid, desc=str(step.get("desc", ""))[:160])
                self.nodes[sid] = node
                self.g.add_node(sid)
            node.n_visit += 1
            node.n_success += int(bool(success))
            node.pos_sum += i / L
            node.pos_n += 1
            if task_type:
                node.task_types[task_type] = node.task_types.get(task_type, 0) + 1
            if question and len(node.examples) < 3:
                node.examples.append(question[:120])
            if not node.desc and step.get("desc"):
                node.desc = str(step["desc"])[:160]
            if prev is not None and prev != sid:
                if self.g.has_edge(prev, sid):
                    self.g[prev][sid]["weight"] += w
                    self.g[prev][sid]["count"] += 1
                    self.g[prev][sid]["succ"] += int(bool(success))
                else:
                    self.g.add_edge(prev, sid, weight=w, count=1, succ=int(bool(success)))
            prev = sid

    # --- task-conditioned subgraph selection = consensus success path ---
    def _seed(self, question: str, top_seeds: int = 3, min_visit: int = 1) -> list[str]:
        pool = [n for n in self.nodes.values() if n.n_visit >= min_visit]
        if not pool:
            return []
        corpus = [f"{n.id.replace('_',' ')} {n.desc} {' '.join(n.examples)}".lower().split()
                  for n in pool]
        bm = BM25Okapi(corpus)
        scores = bm.get_scores(question.lower().split())
        # tie-break / prior toward high-success, frequently-visited steps
        ranked = sorted(
            range(len(pool)),
            key=lambda i: -(scores[i] + 0.25 * pool[i].success_rate + 0.05 * pool[i].n_visit),
        )
        return [pool[i].id for i in ranked[:top_seeds]]

    def select_subgraph(self, question: str, top_seeds: int = 3, max_nodes: int = 8,
                        min_edge_succ: int = 1) -> list[str]:
        """Consensus success-path subgraph: from question-seeded entries, walk the
        highest success-weighted next-step edges to assemble the dominant ordered path(s)
        that succeeded for this kind of task. Returns node ids ordered by avg position."""
        seeds = self._seed(question, top_seeds=top_seeds)
        if not seeds:
            return []
        chosen: set[str] = set(seeds)

        def best_next(sid, seen):
            cands = []
            for _, dst, d in self.g.out_edges(sid, data=True):
                if d.get("succ", 0) >= min_edge_succ and dst not in seen:
                    cands.append((dst, d["weight"]))
            return max(cands, key=lambda x: x[1])[0] if cands else None

        def best_prev(sid, seen):
            cands = []
            for src, _, d in self.g.in_edges(sid, data=True):
                if d.get("succ", 0) >= min_edge_succ and src not in seen:
                    cands.append((src, d["weight"]))
            return max(cands, key=lambda x: x[1])[0] if cands else None

        # grow each seed forward then backward along success-weighted edges
        for s in seeds:
            cur = s
            while len(chosen) < max_nodes:
                nxt = best_next(cur, chosen)
                if nxt is None:
                    break
                chosen.add(nxt)
                cur = nxt
            cur = s
            while len(chosen) < max_nodes:
                pv = best_prev(cur, chosen)
                if pv is None:
                    break
                chosen.add(pv)
                cur = pv
            if len(chosen) >= max_nodes:
                break
        return sorted(chosen, key=lambda nid: self.nodes[nid].avg_pos)

    # --- render the selected subgraph into a SKILL.md ---
    def render_skill(self, node_ids: list[str], question: str = "") -> str:
        if not node_ids:
            return ""
        lines = ["# Skill (assembled from the training-trajectory graph)\n"]
        tts = {}
        for nid in node_ids:
            for t, c in self.nodes[nid].task_types.items():
                tts[t] = tts.get(t, 0) + c
        lines.append("## When to use\n"
                     "A procedure distilled from successful past runs on similar OfficeQA "
                     "questions. Follow the steps in order; skip a step only if clearly N/A.\n")
        lines.append("## Procedure")
        for k, nid in enumerate(node_ids, 1):
            n = self.nodes[nid]
            sr = f"{100*n.success_rate:.0f}% succ over {n.n_visit} runs"
            lines.append(f"{k}. **{n.id.replace('_',' ')}** — {n.desc}  _({sr})_")
        return "\n".join(lines) + "\n"

    # --- persistence ---
    def to_json(self) -> str:
        return json.dumps({
            "nodes": {nid: asdict(n) for nid, n in self.nodes.items()},
            "edges": [{"src": u, "dst": v, **d} for u, v, d in self.g.edges(data=True)],
            "stats": self.stats(),
        }, indent=2, ensure_ascii=False)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "ChainGraph":
        d = json.load(open(path, encoding="utf-8"))
        cg = cls()
        for nid, nd in d["nodes"].items():
            cg.nodes[nid] = StepNode(**nd)
            cg.g.add_node(nid)
        for e in d["edges"]:
            cg.g.add_edge(e["src"], e["dst"],
                          weight=e.get("weight", 1.0), count=e.get("count", 1), succ=e.get("succ", 0))
        return cg

    def stats(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": self.g.number_of_edges(),
            "hub_nodes": sorted(
                ((n.id, n.n_visit, round(n.success_rate, 2)) for n in self.nodes.values()),
                key=lambda x: -x[1])[:8],
        }


# ------------------------------------------------------- LLM "draw chain" step
DRAW_SYS = (
    "You convert an OfficeQA agent execution trace into an ordered CHAIN of canonical, "
    "REUSABLE operation-steps (a 'skill chain'). Each step = ONE semantic operation the agent "
    "performed (e.g. locate_source_document, parse_target_table, extract_requested_figure, "
    "normalize_units_or_format, verify_against_source, emit_answer). Abstract away "
    "question-specific facts. CRITICAL: when an operation matches an existing canonical step in "
    "the provided registry, REUSE that exact id — only mint a new snake_case id when none fits. "
    "This is what lets different trajectories merge at shared nodes."
)


def draw_chain(client, model: str, question: str, trace_text: str, registry: str) -> list[dict]:
    user = (
        f"Existing canonical steps you SHOULD reuse when the operation matches:\n{registry}\n\n"
        f"Question:\n{question[:400]}\n\n"
        f"Execution trace (truncated):\n---\n{trace_text[:11000]}\n---\n\n"
        "Return ONLY a JSON array of 4-9 ordered steps, each "
        '{"id": "<canonical snake_case id>", "desc": "<one-line reusable operation>"}. '
        "No prose."
    )
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": DRAW_SYS},
                  {"role": "user", "content": user}],
        extra_body={"enable_thinking": False}, max_tokens=1200, temperature=0.0)
    txt = r.choices[0].message.content or ""
    for frag in re.findall(r"\[[\s\S]*\]", txt):
        try:
            arr = json.loads(frag)
        except Exception:
            continue
        out = [{"id": str(o.get("id") or o.get("desc", "step")), "desc": str(o.get("desc", ""))}
               for o in arr if isinstance(o, dict) and (o.get("id") or o.get("desc"))]
        if out:
            return out
    return []
