\section{Preliminary}
\label{sec:prelim}

% ─────────────────────────────────────────────────────────────
% §Preliminary — 3 paragraphs (Notation / Problem Formalization / Unified View).
% Main variable = skill granularity, instantiated as the stratified skill graph G.
% Prior methods subsumed as special cases of ONE variable; symbols locked to §Method (Eq:node/route) and §Experiments.
% Paradigm names match §Background / §Experiments: (I) monolithic skill, (II) flat skill bank.
% Neutral formalization — no critique of prior work (that lives in §Intro / §Related Work).
% ─────────────────────────────────────────────────────────────

\paragraph{Notation.}
We study trace-to-skill evolution for an agent solving tasks $t \in \mathcal{T}$ with a \textbf{frozen} backbone $\pi$ and a frozen ReAct executor $E$, refining only an external skill library.
Each solved task yields a trajectory distilled into patches and recorded as execution evidence in a \textbf{stratified skill graph} $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$, whose layers hold trace evidence, capabilities, and governance rules.
A skill node $v \in \mathcal{G}_{\text{cap}}$ has a lifecycle $\text{status}(v)\in\{\text{candidate},\text{validated},\text{deployed},\text{retired}\}$, wired by \texttt{depends\_on}, \texttt{composes\_with}, and \texttt{conflicts\_with} edges.
Central to our formulation is the \textbf{skill granularity} $\mathcal{G}$ admits --- atomic, functional, or plan-level nodes --- which conditions the executor through the injected library $\mathcal{L}\subseteq\mathcal{G}$: $\pi_E(\,\cdot \mid t, \mathcal{L})$.
We refer to the subset routed per task as its \textit{minimal executable skill subgraph}.

\paragraph{Problem Formalization.}
Given $\mathcal{T}$ and the frozen pair $(\pi, E)$, the objective is to curate $\mathcal{G}$ and a routing rule that maximize task success at minimal loaded-token cost:
\begin{equation}
\max_{\mathcal{G},\,\mathcal{L}(\cdot)}\ \mathbb{E}_{t \sim \mathcal{T}}\Big[\,\text{succ}\big(E_\pi(t \mid \mathcal{L}(t))\big) - \lambda\,|\mathcal{L}(t)|\,\Big]
\label{eq:objective}
\end{equation}
where $\text{succ}(\cdot)\in\{0,1\}$ is task success, $|\mathcal{L}(t)|$ the loaded-token cost, and $\lambda>0$ trades cost against success.
The central question is therefore \textbf{how to select $\mathcal{L}(t)$ from $\mathcal{G}$}: we set $\mathcal{L}(t)=\mathcal{S}^\star(t)$, the minimal executable subgraph returned by a routing rule $f_{\mathcal{G}}$ designed in \Cref{sec:method}.

\paragraph{Unified View: a Granularity Sweep.}
Crucially, the granularity $\mathcal{G}$ admits and how $\mathcal{L}(t)$ is drawn from it vary across paradigms, \textbf{subsuming prior skill stores as special cases of one variable}.
For \textbf{(I) monolithic skill} (e.g., Trace2Skill~\citep{trace2skill}), $\mathcal{G}$ \textbf{collapses to a single plan-level node} $d$ with no edges, so $\mathcal{L}(t)=d$ loads \textbf{in full} regardless of relevance.
For \textbf{(II) flat skill bank} (e.g., the curated store of SkillOpt~\citep{skillopt}), nodes are \textbf{atomic but edgeless} ($\mathcal{E}=\varnothing$), so $\mathcal{L}(t)$ is a \textbf{top-$k$ slice} with no dependency or governance structure.
Selecting $\mathcal{L}(t)$ then reduces to a dependency-complete, governed subgraph:
\begin{equation}
\mathcal{S}^\star(t) \;=\; \underbrace{\text{closure}_{\texttt{depends\_on}}\big(\text{seed}_k(t)\big)}_{\text{dependency-complete}} \;\setminus\; \underbrace{\text{blocked}(\mathcal{G}_{\text{gov}})}_{\text{governed-out}}
\label{eq:route-prelim}
\end{equation}
which degenerates to case (I) when $\mathcal{G}$ is one node and to case (II) when $\mathcal{E}=\varnothing$ and governance is empty.
\textbf{Our SkillStrata occupies the full sweep}: $\mathcal{G}$ spans \textbf{all three granularities at once} as a stratified, edge-wired, governed graph, loading only $\mathcal{S}^\star(t)$ --- neither a full monolith nor a structureless top-$k$ slice.
