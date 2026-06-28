\section{Related Work}
\label{sec:related}

% ─────────────────────────────────────────────────────────────
% 3 subsections, each: classification 总句 → (I)(II)(III) paradigm dump → 句5 "falls within X yet differs through Y" 归属句.
% §A = direct alignment (R32 hook NOT here). §B = building blocks. §C = single-layer skill graphs we SUBSUME + R32 hook.
% Differentiation visual = Table (brief Part 4.3, 5 boolean axes). Asset gate WAIVED (no _asset_inventory.json on disk):
%   \Cref{tab:differentiation} kept, wrapped with a TODO. PARAGRAPH_CAP=0 honored: \subsection headers + \paragraph 仅 R32 例外.
% The §Background "Skill Bloat vs. Skill Governance" subsection names the common flaw; here we only classify competitors.
% ─────────────────────────────────────────────────────────────

\subsection{Trace-to-Skill and Self-Evolving Skill Libraries}
\label{sec:related:a}
Methods that distill reusable skills from execution traces and continually update them can be broadly categorized into three classes:
\textbf{(I) monolithic merge}, which hierarchically reduces distilled patches into a single ever-growing skill document loaded in full at inference, as in Trace2Skill~\citep{trace2skill} and SkillBrew~\citep{skillbrew};
\textbf{(II) optimization-gated curation}, which edits a skill store under a held-out validation gate, accepting only edits that do not regress, as in SkillOpt~\citep{skillopt} and the curation learner of \citet{skillos_ouyang};
and \textbf{(III) self-evolving update loops}, which iteratively grow a skill set across a lifelong task stream~\citep{evoskill}.
Our \textbf{SkillStrata} falls within \textbf{this self-evolving line}, yet \textbf{distinguishes itself} from prior approaches through its dedicated \textbf{refactor-style \textsc{Split}} operator, which decomposes a coarse skill into atomic, separately-addressable capabilities, as well as its \textbf{dependency-aware routing of a minimal executable subgraph}, rather than the monolithic full-load or non-decreasing document edits these methods apply.

\subsection{Graph Memory and OS-Style Lifecycle}
\label{sec:related:b}
A parallel line organizes an agent's accumulated experience as a structured, governed store, falling into two classes:
\textbf{(I) hierarchical graph memory}, which arranges past interactions into a multi-level graph traversed by $k$-hop retrieval, as in G-Memory~\citep{gmemory};
and \textbf{(II) OS-style lifecycle memory}, which schedules memory by a heat signal and promotes or evicts entries over time, as in MemoryOS~\citep{memoryos} and MemOS~\citep{memos}.
Our \textbf{SkillStrata} falls within \textbf{this graph-and-lifecycle paradigm}, yet \textbf{distinguishes itself} from prior approaches through its target object being a \textbf{governed \emph{skill} library rather than a memory store}, organized by stable slug identifiers in place of raw-task-string nodes, as well as its \textbf{dependency-aware \textsc{Split}/\textsc{Route} operators}, rather than the promotion-and-eviction lifecycle these methods apply to opaque memory items.

\subsection{Skill Graphs and Dependency-Aware Routing}
\label{sec:related:c}
Closest to our routing mechanism, a recent line represents skills as a graph and selects among them at inference, falling into two classes:
\textbf{(I) reinforcement-trained skill graphs}, which learn to traverse a skill graph via RL, as in SkillGraph-RL~\citep{skillgraph_rl};
and \textbf{(II) retrieval-and-composition over a fixed skill graph}, which routes or sequences existing skill nodes for a task, as in Graph-of-Skills~\citep{gos} and SkillGraph-ToolSeq~\citep{skillgraph_toolseq}.
Our \textbf{SkillStrata} falls within \textbf{this skill-graph paradigm}, yet \textbf{distinguishes itself} from prior approaches through its \textbf{three-layer stratification of trace, capability, and governance}, as well as its \textbf{test-time assembly of a missing skill from trace sub-parts}, rather than the single-layer routing of already-fixed skills these methods perform --- which SkillStrata \textbf{subsumes as the in-domain special case} of assembly.
\paragraph{}
While all these graph methods aim to reuse skills by routing or composing nodes that already exist, they operate on a single layer of fixed capabilities. \textbf{We are not aware of previous attempts to, beyond routing existing skills in-domain, synthesize a fit skill out-of-domain at test time by drilling into the trace-layer evidence beneath the capability graph.}

% ─────────────────────────────────────────────────────────────
% Differentiation visual: Table B (brief Part 4.3). 5 boolean axes prior methods do NOT jointly satisfy; Ours row all-cmark.
% \cmark/\xmark from pifont (\usepackage{pifont}; \newcommand{\cmark}{\ding{51}}\newcommand{\xmark}{\ding{55}}).
% ─────────────────────────────────────────────────────────────
\begin{table}[t]
\centering\small
\caption{\textbf{Differentiation along five axes that prior skill systems do not jointly satisfy.} One representative method per family; SkillStrata is the only system that is simultaneously modular, dependency-linked, refactorable, dependency-routed, and lifecycle-governed.}
\label{tab:differentiation} % TODO: add Part 12 inventory row for tab:differentiation (asset inventory absent; gate waived)
\begin{tabular}{@{}llccccc@{}}
\toprule
Family & Method & \makecell{Modular\\skills?} & \makecell{Dependency\\edges?} & \makecell{Refactor\\\textsc{Split}?} & \makecell{Dependency-aware\\routing?} & \makecell{Lifecycle\\governance?} \\
\midrule
Monolithic merge   & Trace2Skill~\citep{trace2skill}     & \xmark & \xmark & \xmark & \xmark & \xmark \\
Flat skill bank    & Top-$k$ retrieval                   & \cmark & \xmark & \xmark & \xmark & \xmark \\
Optimization gate  & SkillOpt~\citep{skillopt}           & \xmark & \xmark & \xmark & \xmark & \cmark \\
Graph memory       & G-Memory~\citep{gmemory}            & \cmark & \cmark & \xmark & \xmark & \cmark \\
Single-layer skill graph & SkillGraph-RL~\citep{skillgraph_rl} & \cmark & \cmark & \xmark & \cmark & \xmark \\
\midrule
\textbf{Stratified system} & \textbf{SkillStrata (Ours)} & \textbf{\cmark} & \textbf{\cmark} & \textbf{\cmark} & \textbf{\cmark} & \textbf{\cmark} \\
\bottomrule
\end{tabular}
\end{table}
