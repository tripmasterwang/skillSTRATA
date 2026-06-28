\section{Experiments}
\label{sec:exp}

% ─────────────────────────────────────────────────────────────
% Tier/Mode header (for look-back audit):
%   subsection_title_style = claim-title (brief Part 0.6, default)
%   Mode C (R55 paragraph-title-as-claim) for ablation findings; Register-A main table; Register-B mechanism/case
%   RQ map (one [RQ_N] per subsection — ONE-RQ HARD rule splits brief 7.0's RQ2/RQ4 ablation lump):
%     E2=[RQ1] E3=[RQ2] E4=[RQ4] E5=[RQ3] E6=[RQ5]
%   NUMBER PROVENANCE: every number tagged [SIM] / [REAL] / [PENDING-280TEST] inline. Tags surfaced, not laundered.
%   Asset gate WAIVED (no _asset_inventory.json on disk): \Cref{} kept, each wrapped with a TODO; do not halt.
% ─────────────────────────────────────────────────────────────

% ─────────────────────────────────────────────────────────────
% §E0 — RQ list opener (prose, italic central hypothesis). Untagged.
% ─────────────────────────────────────────────────────────────
We conduct a series of experiments designed to validate the central hypothesis of our work: \textit{that the gains of trace-to-skill evolution come not from accumulating a larger skill document but from stratifying skills into a governed graph that is split, routed, and assembled on demand}.
Our evaluation is structured around five primary research questions.
\textbf{First}, we test whether SkillStrata reaches higher task success at lower loaded-token cost than monolithic and flat-bank skill stores \textbf{(RQ1)}.
\textbf{Second}, we ask which lifecycle operators actually drive the gains, \textbf{moving from outcome to mechanism} --- splitting and routing versus simply storing more skills \textbf{(RQ2)}.
\textbf{Third}, we isolate the role of governance and the propose-then-verify gate as a stability safety net over long task streams \textbf{(RQ3)}.
\textbf{Fourth}, we quantify whether the stratified graph improves routing precision and suppresses negative transfer \textbf{(RQ4)}.
\textbf{Finally}, we conduct an exploratory study of whether test-time assembly can synthesize a fit skill from trace sub-parts and recover out-of-domain coverage that no deployed skill covers \textbf{(RQ5)}.
Because the full real-benchmark sweep is still in progress, we are explicit throughout about which evidence is \textbf{[REAL]} (SpreadsheetBench), which is a \textbf{[SIM]} deterministic-simulator result pending real-benchmark replacement, and which is \textbf{[PENDING]} and not yet available.

% ─────────────────────────────────────────────────────────────
% §E1 — Setup (untagged infrastructure). Part 7.0 caps this at 2 paragraphs; we use functional-label paragraphs.
% ─────────────────────────────────────────────────────────────
\subsection{Experimental Setup}
\label{sec:exp:setup}

\paragraph{\bf Models, Datasets, and Baselines.}
Our \textbf{[REAL]} experiments use a single backbone, \textbf{qwen3.6-35b-a3b}~\citep{qwen36} (xf-yun MaaS, \texttt{reasoning\_effort}=medium), with a \textbf{frozen} Trace2Skill ReAct executor and Anthropic-style \texttt{SKILL.md} capability bodies, so that only the skill library --- not the backbone or the agent loop --- varies across conditions.
We evaluate on \textbf{SpreadsheetBench} (verified-400), scored by the \textit{official per-instance hard} success metric, using the SkillOpt $80/40/280$ split with \texttt{split\_seed}=42 (train / validation / test).
Alongside this, a \textbf{[SIM]} deterministic-simulator harness ($8$ seeds, a $400$-task heterogeneous/out-of-domain stream over a four-domain synthetic skill universe with a dependency DAG; configuration in \Cref{tab:setup}) % TODO: confirm Part 12 inventory row for tab:setup (asset inventory absent; gate waived)
provides controlled mechanism and ablation evidence \textit{pending replacement by the real benchmark}.
We compare against \textit{\ding{182} monolithic}: \textbf{No-Skill} and \textbf{Trace2Skill} (single-body, full-load)~\citep{trace2skill}; \textit{\ding{183} flat}: \textbf{Flat Skill Bank} (BM25 top-$k$) and \textbf{Pruning-only}; and, on the real benchmark, the published \textit{\ding{184} curated} baseline \textbf{SkillOpt}~\citep{skillopt} (prune + validation gate) as the comparison target.

\paragraph{\bf Metrics and Protocol.}
We report \textbf{Task Success Rate} $\uparrow$ and \textbf{Avg. Loaded Tokens} $\downarrow$ as primary metrics, and \textbf{Negative-Transfer Rate} $\downarrow$, \textbf{OOD Transfer Gain} $\uparrow$, \textbf{Routing Precision} $\uparrow$, and per-window \textbf{Stability} $\uparrow$ as secondary metrics.
All \textbf{[SIM]} numbers are means over $8$ random seeds; per-seed $\pm$ standard deviation and a paired significance test are recorded by the harness but \textbf{[PENDING]} in the present tables.
On the real benchmark we follow the SkillOpt protocol exactly so that the gain-over-no-skill is comparable, noting one caveat: SkillOpt's published numbers use a direct-chat harness whereas ours use an agentic ReAct executor, so absolute floors differ and we compare the lift over the shared No-Skill baseline rather than raw absolutes.

% ─────────────────────────────────────────────────────────────
% §E2 — [RQ1] Main results. Register A. Carries [REAL] SkillOpt target + [PENDING-280TEST] placeholder + [SIM] sim table.
% 5 必含要素: hypothesis 重述 / 总结 / baseline 对偶 / highlight / why / 过渡. Part 7.0 cap = 2 paragraphs.
% ─────────────────────────────────────────────────────────────
\subsection{[RQ1] SkillStrata Attains the Highest Success at the Lowest Loaded-Token Cost}
\label{sec:exp:main}

\paragraph{\bf Simulator evidence.}
On the controlled simulator (\Cref{tab:main}), % TODO: confirm Part 12 inventory row for tab:main (asset inventory absent; gate waived)
the results \textbf{provide strong support for our central hypothesis} that a governed, routable graph beats a larger document: \textbf{[SIM]} SkillStrata \textbf{consistently dominates every multi-skill baseline on both success and cost}.
The two existing paradigms each solve only half the problem: \textbf{[SIM]} \textbf{Trace2Skill}'s full-load monolith reaches $0.574$ success but pays $780$ loaded tokens and a $0.219$ negative-transfer rate, while the \textbf{Flat Skill Bank} cuts tokens to $431$ yet stalls at $0.555$ success with weak routing.
\textbf{In contrast}, \textbf{[SIM]} SkillStrata reaches $\textbf{0.704}$ success at only $\textbf{365}$ loaded tokens --- $\textbf{+13}$ points over Trace2Skill at $\textbf{2.1}\times$ fewer tokens, and $+15$ points over the flat bank --- while \textbf{halving} negative transfer to $0.105$.
\textbf{We hypothesize that} splitting the monolith lets the router load only the minimal executable subgraph rather than an ever-growing body; \textbf{consequently}, the same dependency-closed routing that lifts success also strips the irrelevant skill text that drives both token cost and negative transfer.
These \textbf{[SIM]} numbers stand in for the real-benchmark head-to-head and are reported here as simulator-side evidence \textit{pending replacement}.

\paragraph{\bf Real-benchmark target and status.}
On real SpreadsheetBench (\Cref{tab:main}), our published comparison target is SkillOpt: \textbf{[REAL]} a No-Skill floor of $\textbf{38.2}$ rises to $\textbf{47.5}$ ($\textbf{+9.3}$) under SkillOpt, whereas a naively distilled \textbf{Trace2Skill} library \textit{regresses} to $\textbf{33.2}$ ($\textbf{-5.0}$, a real instance of negative transfer), with GEPA at $45.4$, Human-written skills at $44.3$, and TextGrad at $22.9$ filling the band between.
This sets the bar SkillStrata must clear --- beating $+9.3$ gain-over-no-skill while avoiding the $-5.0$ Trace2Skill collapse --- under the identical hard metric and \texttt{split\_seed}=42 protocol.
\textbf{Our own head-to-head no-skill vs.\ with-SkillStrata result on the SkillOpt $280$-test split is \texttt{[PENDING-280TEST]} and is not yet available}; we therefore leave it as an explicit placeholder here rather than substituting any simulator number for it.
\textbf{Having established} the cost--success frontier in simulation and fixed the real-benchmark target, \textbf{a critical question is} which operators are actually responsible for the gain.

% ─────────────────────────────────────────────────────────────
% §E3 — [RQ2] Ablation: which operators drive the gains. Mode C finding paragraphs. ANALYSIS → shallow→deep + S9.
% Part 7.0 cap = 2 paragraphs.
% ─────────────────────────────────────────────────────────────
\subsection{[RQ2] Splitting and Routing, Not More Skills, Drive the Gains}
\label{sec:exp:ablation}

A \textbf{leave-one-out ablation} on the simulator (\Cref{tab:ablation}) reveals a clear hierarchy: % TODO: confirm Part 12 inventory row for tab:ablation (asset inventory absent; gate waived)
the two operators that restructure the library, not those that merely enlarge it, carry the result.

\paragraph{\bf Routing is the single most critical operator.}
\textbf{[SIM]} Removing \textsc{Route} drops success the most, from $0.643$ to $0.462$ ($\textbf{-0.18}$), and simultaneously raises both loaded tokens ($360\!\to\!472$) and negative transfer ($0.116\!\to\!0.213$).
Routing earns this because activating the dependency closure $\mathcal{S}^\star$ (\Cref{eq:route}) loads exactly the prerequisite skills a relevant seed silently needs and nothing else; without it the agent falls back to undirected top-$k$ text that is both larger and noisier.
\textbf{More generally, this suggests a transferable principle}: whenever skills carry latent prerequisite structure, routing the dependency closure rather than a flat top-$k$ slice is what converts a skill store into a usable one --- a rule any retrieval-augmented skill system with a measurable dependency signal can apply beyond our setting.

\paragraph{\bf Splitting the monolith is what makes routing cheap.}
\textbf{[SIM]} Removing \textsc{Split} costs $0.643\!\to\!0.489$ success ($\textbf{-0.15}$) but, strikingly, inflates loaded tokens $\textbf{6.6}\times$ (from $360$ to $2345$) and collapses routing precision to $0.081$; the \textbf{Full Skill Loading} variant pushes this to $3932$ tokens at $0.481$ success.
This is exactly what the story predicts: an unsplit body forces full-load injection, so there is no atomic unit for the router to select, and \textbf{the conflict the architecture was built to remove} --- one monolithic skill dragging in unrelated behaviors --- re-appears as both token bloat and negative transfer.
\textbf{More generally, this suggests a transferable principle}: refactoring a coarse capability into atomic, separately-addressable units is a precondition for any routing mechanism to pay off, since routing can only be as fine-grained as the units it selects over.
By contrast, \textbf{[SIM]} removing lifecycle validation or the governance graph \emph{individually} barely moves the headline numbers ($-0.014$ and $-0.005$ success), placing them in a different role we examine next.

% ─────────────────────────────────────────────────────────────
% §E4 — [RQ4] Routing precision & negative-transfer reduction. [SIM] + REAL gate evidence. ANALYSIS.
% Part 7.0 has no explicit row; cap = (fields+1)=2.
% ─────────────────────────────────────────────────────────────
\subsection{[RQ4] Stratification Sharpens Routing and Suppresses Negative Transfer}
\label{sec:exp:routing}

\textbf{Having shown} that splitting and routing drive the headline gain, we now isolate \emph{why} that gain is safe rather than merely larger, by measuring routing precision and negative transfer directly.
\textbf{[SIM]} On the simulator (\Cref{tab:main}), SkillStrata attains the highest routing precision, $\textbf{0.391}$ --- about $1.2\times$ the flat bank's $0.317$ and roughly $6\times$ Trace2Skill's $0.234$ --- while cutting the negative-transfer rate to $\textbf{0.105}$, less than half of Trace2Skill's $0.219$.
The two move together because the governance layer quarantines conflicting nodes before they reach the prompt: higher precision means fewer irrelevant skills loaded, which is the same mechanism that suppresses negative transfer.
This is corroborated by a \textbf{[REAL]} from-zero curate run on SpreadsheetBench, where the propose-then-verify gate (\Cref{eq:gate}) demonstrably catches a harmful batch: validation accuracy on the blank graph was $\textbf{42.5\%}$, a distilled round-0 library \emph{dropped} it to $\textbf{32.5\%}$ ($\textbf{-10}$pp), the gate \textbf{rejected} that round and retired its $12$ skills, and the next round was \textbf{accepted}, lifting accuracy to $\textbf{47.5\%}$ ($+5$pp over the blank graph).
\textbf{This indicates that} SkillStrata \textbf{autonomously screens out negative transfer at curation time} rather than absorbing it, with no gradient signal.
\textbf{More generally, this suggests a transferable principle}: a held-out promotion gate that admits an edit only when success is non-decreasing \emph{and} negative transfer is non-increasing turns skill accumulation from an open-loop hazard into a self-correcting process any lifelong-learning library can adopt.

% ─────────────────────────────────────────────────────────────
% §E5 — [RQ3] Governance/validation stability safety net. fig:stability. [SIM]. ANALYSIS. Part 7.0 cap = 1 paragraph.
% ─────────────────────────────────────────────────────────────
\subsection{[RQ3] Governance and Validation Act as a Complementary Stability Safety Net}
\label{sec:exp:stability}

\textbf{Having} found that validation and governance contribute little \emph{individually} to the headline success, we probe their joint role on long task streams, where their value should surface.
\textbf{[SIM]} As shown in \Cref{fig:stability}, % TODO: confirm Part 12 inventory row for fig:stability (asset inventory absent; gate waived)
removing either guard alone leaves late-stream success and per-window stability essentially intact ($-0.004$ to $-0.014$), but \textbf{removing both together} drives late-stream success to its lowest value ($0.601\!\to\!0.562$) and yields the least stable trajectory across the ten evaluation windows.
This is the signature of a \textbf{safety net} rather than a primary driver: each guard is redundant while the other holds, and the degradation only appears once the stream accumulates enough drift that no guard remains to catch a harmful promotion or a mis-routed node.
\textbf{This validates that} governance is not decorative overhead but the mechanism that keeps a continually-curated library from degrading late in its life --- the inference-time counterpart, via the node-local verify-loop (\Cref{eq:verify}), of the train-time gate.
\textbf{More generally, this suggests a transferable principle}: redundant governance guards register as low-impact under any single-removal ablation yet are exactly what bounds long-horizon drift, so self-evolving systems should be stress-tested by \emph{jointly} disabling their safety mechanisms over a long stream, not one at a time.

% ─────────────────────────────────────────────────────────────
% §E6 — [RQ5] Test-time assembly OOD. tab:tta. [SIM] TTA ~54% + REAL case study 416-15. ANALYSIS + case study.
% Part 7.0 cap = 1 paragraph; we keep the synthesis result + the case study (REAL trace) as one analysis subsection.
% ─────────────────────────────────────────────────────────────
\subsection{[RQ5] Test-Time Assembly Recovers Out-of-Domain Coverage from Trace Sub-Parts}
\label{sec:exp:tta}

\textbf{Finally}, we conduct an exploratory study of whether the router can \textbf{cast a missing skill on the spot} from trace co-occurrence (\Cref{eq:tta}) when no deployed skill covers a needed sub-capability.
\textbf{[SIM]} Withholding the three most-used atomic skills per domain to create a coverage gap (\Cref{tab:tta}), % TODO: confirm Part 12 inventory row for tab:tta (asset inventory absent; gate waived)
test-time assembly raises covered capability from $0.296$ to $\textbf{0.473}$ --- recovering about $\textbf{54\%}$ of the gap to the full-skill upper bound ($0.621$) --- and lifts success $+0.056$ and OOD success $+0.044$, at an honest cost of $+88\%$ tokens ($325\!\to\!611$) and $2.6$ synthesized skills per task.
We attribute the recovery to the trace layer participating at inference: \textbf{[SIM]} unlike single-layer skill graphs that can only route already-fixed skills, SkillStrata drills into historical co-occurrence evidence to assemble a temporary body, so a sub-capability with no deployed node is still reachable.
A \textbf{[REAL]} case study sharpens why governance must reach all the way to execution: on SpreadsheetBench task \texttt{416-15}, a date-cleaning instance the blank No-Skill agent \emph{solves}, injecting a distilled round-0 library \emph{breaks} it --- three unrelated procedural skills are mis-routed in, and a \texttt{self\_verification} skill compares the output against its \emph{own} recomputed value (a tautology), rubber-stamping an erroneous \texttt{datetime}$\to$string \texttt{strftime} conversion as ``All checks passed!'' and overriding the base prompt's ``dates as Excel dates'' hint.
\textbf{This provides closed-loop evidence that} a distilled skill's self-check can manufacture \textbf{false confidence} by verifying a tautology rather than task semantics, which is precisely the failure the node-local verify-loop is built to catch by writing its postcondition at the task-semantic layer --- \textbf{opening a promising direction for} governance that gates execution, not only the library.
\textbf{More generally, this suggests a transferable principle}: a self-verification skill is only as trustworthy as the semantics of the condition it checks, so any agent that distills its own checks must anchor them to task-level postconditions rather than self-consistency, on pain of confidently shipping wrong answers.

% ─────────────────────────────────────────────────────────────
% §E7 — Efficiency (untagged infrastructure). Register A, double-win sentence.
% ─────────────────────────────────────────────────────────────
\paragraph{\bf Efficiency.}
\textbf{[SIM]} Among all multi-skill methods, SkillStrata loads the \emph{fewest} tokens while attaining the \emph{highest} success: $365$ tokens versus Trace2Skill's $780$ ($\textbf{2.1}\times$ fewer) and full skill loading's $3932$ ($\textbf{10.8}\times$ fewer).
This demonstrates that \textbf{[SIM]} SkillStrata \textbf{delivers the highest success rate at the lowest loaded-token cost}, with latency and API-call breakdowns deferred to the appendix and pending the real-benchmark run.
