\section{Introduction}
\label{sec:intro}

% ─────────────────────────────────────────────────────────────
% FINAL_PLAYBOOK §3 — 6 paragraphs, ~22–28 sentences, ~500–700 words.
% Reframe 招式 = AgentFlow (verb-role component naming: organize → govern → route → assemble).
% 段1 style = A trend-dump. 段3 RQ = A obsbox. External-discipline anchor (complex networks /
%   hierarchical multilayer network, boccaletti2014multilayer) introduced HERE in 段1.2; §M0 only recalls it.
% PROVENANCE: every empirical claim tagged [REAL]/[SIM]/[PENDING] inline; 280-test = [PENDING], never fabricated.
% 大终点词 = self-evolving agents (echo abstract句1 / conclusion句4).
% ─────────────────────────────────────────────────────────────

% ── 段 1: Big environment + subdomain (trend-dump) + external-discipline anchor ──
The ascent of LLM agents that \emph{self-evolve} by distilling reusable skills from their own execution traces marks a paradigm shift across embodied control, spreadsheet automation, and scientific discovery~\citep{trace2skill,skillopt,skillbrew,evoskill,gmemory,memoryos,skillos_ouyang}.
Pivotal to this self-evolution is the agent's \textbf{skill library}, the store of trace-distilled procedures that conditions future behavior with a frozen backbone.
Research on \textbf{complex networks} offers a familiar template for how such an accumulating store should be organized: a \emph{hierarchical multilayer network} places raw evidence at the bottom and lets higher layers \emph{operate on top} of it~\citep{boccaletti2014multilayer}, so that structure, not bulk, governs what is used.
The open question is thus no longer \emph{whether} an agent should accumulate skills, but \emph{how} that growing library should be structured to stay usable over a lifetime of tasks.

% ── 段 2: Two-paradigm conflict (信息密度最高) ──────────────────
% 句2.0 route-shift lead-in (brief 3.2 NON-[无]) → two paradigms (I)(II) + flaws → 句2.6 named common flaw.
Trace-to-skill methods implicitly equate a more heavily merged skill with a stronger one --- a premise that holds early but, over a long horizon, breeds bloated documents polluted by conflicting rules; the focus must therefore shift from \emph{making a bigger document} to \emph{governing modular skills}, a goal pursued by two dominant paradigms.
The first is \textbf{(I) monolithic skill}, which merges distilled patches into one ever-growing document loaded in full at inference~\citep{trace2skill,skillbrew,skillopt}; its reliance on full-load injection inevitably entails \textbf{skill bloat} and \textbf{negative transfer}.
Conversely, the second is \textbf{(II) flat skill bank}, which stores skills as independent entries and retrieves a top-$k$ slice~\citep{skillgraph_rl,gos}; with no dependency closure and no governance, its similarity-based routing silently \textbf{mis-routes}, omitting prerequisites and admitting conflicts.
Both reduce skill evolution to mere \emph{accumulation}, leaving the library \textbf{ungoverned}: neither can split a coarse skill, route its dependencies, or retire a harmful one --- a tension we name \textbf{Skill Bloat versus Skill Governance}.

% ── 段 3: Emerging direction + RQ (概念发明集中处) ──────────────
Given these deficiencies, organizing accumulated experience as a \textbf{structured, governed store} --- a graph with an explicit lifecycle, not a flat bag of entries --- offers a compelling alternative.
Existing efforts either build \textbf{(i) hierarchical graph memory}~\citep{gmemory}, which keys nodes on raw task strings with no stable skill identity; or maintain \textbf{(ii) OS-style lifecycle memory}~\citep{memoryos,memos}, which promotes and evicts \emph{memory items} rather than skills with dependencies.
Nevertheless, both diverge from a usable skill store in \textbf{two critical dimensions}: no \emph{refactoring} of a coarse capability into atomic units, and no \emph{dependency-aware routing} of the minimal set a task needs --- the algorithmic analogue of \emph{stratifying} the library so higher layers \emph{operate on top} of raw trace evidence~\citep{boccaletti2014multilayer}, each task drawing a \textit{minimal executable skill subgraph}.
\begin{obsbox}
\textit{Should skill evolution end in ever-larger documents, or in a governable, composable, and routable skill graph?}
\end{obsbox}

% ── 段 4: Method + callback (结构核心, AgentFlow verb-role naming) ──
To address this challenge, we introduce \textbf{SkillStrata}, a stratified skill \textbf{system} that curates trace-to-skill evolution into a \textbf{Skill Strata} graph $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$ of trace evidence, capabilities, and governance, where higher layers operate on top of raw evidence (\Cref{fig:framework}).
At its core, SkillStrata coordinates three verb-roles: it \textbf{organizes} distilled patches into modular skill nodes; it \textbf{governs} them through refactor-style \textsc{Split}, \textsc{Merge}, \textsc{Link}, and \textsc{Retire} operators behind a \textbf{propose-then-verify} gate, with no gradients and no reinforcement learning; and it \textbf{routes} a \textbf{minimal executable skill subgraph} per task.
Unlike \textbf{(I) monolithic merge}, which invites \textbf{skill bloat}, and \textbf{(II) flat top-$k$ retrieval}, which leaves the library \textbf{ungoverned}, SkillStrata \textbf{splits the monolith into a governed graph and routes only a dependency-complete subgraph}.
At test time it \textbf{assembles} skills like LEGO bricks --- routing existing skills in-domain and casting a missing one from trace sub-parts out-of-domain --- guarded by a node-local verify-loop where a distilled skill might rubber-stamp its own error.

% ── 段 5: Empirical Highlights (★ PROVENANCE-respecting, MIXED [REAL]/[SIM]/[PENDING]) ──
We evaluate SkillStrata on \textbf{[REAL]} SpreadsheetBench (\texttt{qwen3.6-35b-a3b}, the SkillOpt split) and a \textbf{[SIM]} deterministic simulator for controlled ablations.
Against the published \textbf{[REAL]} \textbf{SkillOpt} target, a No-Skill floor of $38.2$ rises to $47.5$ ($+9.3$) while a naively distilled \textbf{Trace2Skill} library \emph{regresses} to $33.2$ ($-5.0$, real negative transfer) --- the bar SkillStrata must clear.
Crucially, a \textbf{[REAL]} from-zero curate run shows the \textbf{propose-then-verify gate working}: a harmful round drops validation accuracy from $42.5\%$ to $32.5\%$, the gate \textbf{rejects} it (retiring $12$ skills), then \textbf{accepts} the next, lifting accuracy to $47.5\%$ --- negative transfer screened out with no gradient signal.
On the simulator, \textbf{[SIM]} SkillStrata attains the highest success ($0.704$ vs.\ Trace2Skill's $0.574$) at the lowest token cost ($365$ vs.\ $780$), while the full \textbf{[REAL]} $280$-test head-to-head is \textbf{[PENDING]}.
\textbf{More importantly}, our ablation shows these gains come from \textbf{splitting and routing, not amassing more skills} --- removing \textsc{Split} or \textsc{Route} inflates tokens up to $6.6\times$ --- evidence that for \textbf{self-evolving agents}, structure beats bulk.

% ── 段 6: Contributions (3 core, task → method → effect; no release item) ──
Our contributions are threefold:
\begin{itemize}[leftmargin=*, itemsep=0pt]
    \item We \textbf{introduce} the problem of curating a \emph{stratified skill system} rather than a single skill, instantiated as \textbf{SkillStrata}, a governed three-layer graph that subsumes single-layer skill-graph methods as its in-domain special case.
    \item We \textbf{propose} a gradient-free \textbf{curate} loop --- refactor-style \textsc{Split} and dependency-aware \textsc{Route} under a propose-then-verify gate --- with test-time \textbf{LEGO assembly} and a node-local verify-loop that gates execution as well as the library.
    \item We \textbf{show} that the gate autonomously rejects a harmful batch yet accepts a beneficial one on a real benchmark \textbf{[REAL]}, and that SkillStrata attains the highest success at the lowest token cost \textbf{[SIM]}, with the real-benchmark head-to-head \textbf{[PENDING]}.
\end{itemize}
