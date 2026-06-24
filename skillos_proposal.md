# SkillOS: A Hierarchical Graph-Governed Skill System for LLM Agents

## Optional Subtitle

**From Monolithic Skill Documents to Modular Skill Composition and Routing**

## Abstract

Existing trace-to-skill methods usually compress agent trajectories into reusable skill documents, and improve downstream task performance through continuous update and merge operations. However, such methods can easily lead to increasingly large monolithic skills, while lacking a systematic mechanism for skill splitting, composition, dependency modeling, routing, and lifecycle governance.

We propose **SkillOS**, a hierarchical graph-governed skill system for LLM agents. Instead of treating skills as a flat skill bank or a small number of large textual documents, SkillOS organizes trajectory-derived experience into a multi-granularity skill graph. Inspired by G-Memory's hierarchical graph organization and MemoryOS's OS-style lifecycle management, SkillOS introduces a three-layer structure: **trace graph**, **capability graph**, and **governance graph**. It further manages skills through lifecycle operations such as promotion, validation, split, merge, link, retire, and dependency-aware routing.

Built on top of a Trace2Skill-style pipeline, SkillOS replaces monolithic hierarchical merge with graph-governed skill curation and routes each task to a minimal executable skill subgraph. Expected experiments show that SkillOS can maintain or improve task success rate while reducing token cost, mitigating negative transfer, and improving cross-task reuse.

## Motivation

Current self-evolving skill methods often assume that:

> The more complete a skill becomes, and the more experience it merges, the stronger it will be.

This assumption works in the short term, but becomes problematic in long-horizon skill evolution.

### Problem 1: Skill Bloat

Single skill documents become increasingly long and contain too many task-specific details. At test time, the agent may need to load large skill documents even when only a small sub-capability is relevant.

### Problem 2: Negative Transfer

A large skill may contain local rules that only apply to a narrow task setting. When the entire skill is loaded for a different task, these local rules can mislead the agent and cause negative transfer.

### Problem 3: Lack of Governance

Existing systems usually support insert, update, delete, or prune operations, but rarely answer the following questions explicitly:

- When should a skill be split?
- Which skills should be composed?
- Which skills depend on or conflict with each other?
- Which sub-skills should be loaded for a given task?
- When should a candidate skill become deployed?
- When should a deployed skill be retired?

Therefore, our goal is not to build another stronger skill generator. Instead, we argue that:

> Skill evolution should not end in larger skill documents; it should produce a governable, composable, and routable modular skill system.

## Claim

### Main Claim

> Existing trace-to-skill methods compress experience into increasingly monolithic skill documents, but lack a principled mechanism for organizing, routing, and governing modular skills. SkillOS addresses this by introducing a hierarchical graph-governed skill system with OS-style lifecycle management.

### Short Claim

> SkillOS turns evolving skills from flat textual documents into a hierarchical, graph-governed skill system.

### Core Innovations

1. **Graph-governed skill organization**

   Skills are no longer represented as flat documents, but as nodes and edges in trace, capability, and governance graphs.

2. **Lifecycle-aware skill governance**

   SkillOS manages the full lifecycle from raw trace to candidate fragment, validated node, deployed skill, split/merged skill, and retired skill.

3. **Dependency-aware skill routing**

   At inference time, SkillOS does not retrieve top-k skill texts. It activates a minimal executable skill subgraph conditioned on the task and graph dependencies.

## Method

## Pipeline

### Original Trace2Skill Pipeline

```text
task trajectories
-> extract skill patches
-> hierarchical merge
-> large skill document
-> retrieve / load skill
-> execute task
```

### SkillOS Pipeline

```text
task trajectories
-> extract skill patches
-> normalize into skill fragments
-> graph-governed split / merge / link
-> hierarchical skill graph
-> dependency-aware routing
-> minimal skill subgraph execution
-> update lifecycle statistics
```

## Hierarchical Graph Structure

SkillOS uses a three-layer graph structure.

### Trace Graph

The trace graph stores execution-level evidence.

```text
Nodes:
  trajectories
  tool calls
  failures
  successes
  examples

Edges:
  temporal_order
  co_occurrence
  caused_failure
  fixed_by
```

### Capability Graph

The capability graph stores modular skills and their relationships.

```text
Nodes:
  atomic skills
  functional skills
  plan-level skills
  tools
  task types

Edges:
  depends_on
  composes_with
  alternative_to
  conflicts_with
  parent_child
```

### Governance Graph

The governance graph stores higher-level rules and decisions.

```text
Nodes:
  governance rules
  split decisions
  merge decisions
  retirement signals

Edges:
  supported_by_trace
  applies_to_skill
  blocks_routing
  promotes_skill
```

## Architectural Inspiration

SkillOS mainly adopts two core architectural inspirations.

### From G-Memory

```text
G-Memory:
interaction graph -> query graph -> insight graph

SkillOS:
trace graph       -> capability graph -> governance graph
```

G-Memory contributes the idea of hierarchical graph organization and bidirectional traversal. In SkillOS, this becomes:

```text
task -> capability -> subskill
governance insight -> constraint -> routing decision
```

### From MemoryOS

```text
MemoryOS:
storage / update / retrieval / generation

SkillOS:
skill storage / skill governance / skill routing / skill execution
```

MemoryOS contributes the OS-style lifecycle framing. In SkillOS, this becomes a lifecycle for skill fragments and skill nodes.

## Skill Lifecycle

```text
raw trace
-> skill patch
-> candidate skill fragment
-> validated skill node
-> deployed skill node
-> split / merged / retired skill
```

### Skill Node Example

```yaml
id: csv_schema_validation
name: CSV Schema Validation
granularity: atomic
description: Check whether CSV columns, types, and missing values match task requirements.
status: candidate
parents:
  - data_cleaning
dependencies:
  - load_csv
  - infer_column_types
conflicts: []
success_count: 18
failure_count: 3
token_cost: 420
last_used: task_183
evidence_traces:
  - trace_041
  - trace_077
```

## Core Operations

SkillOS supports the following governance operations:

```text
INSERT: add a new skill node
UPDATE: update an existing skill node
SPLIT: split an oversized skill into smaller sub-skills
MERGE: merge redundant skills
LINK: add dependency / composition / conflict edges
RETIRE: retire low-utility or high-risk skills
ROUTE: select a minimal skill subgraph for the current task
```

The most important operations are **SPLIT** and **ROUTE**. They distinguish SkillOS from prior systems that mainly focus on insert, update, delete, merge, or pruning.

## Training-Time Input and Output

### Input Example

```json
{
  "task_id": "wiki_table_042",
  "task": "Answer a question based on a table with inconsistent date formats.",
  "trajectory": [
    "Loaded table",
    "Parsed date column as string",
    "Filtered rows incorrectly",
    "Final answer wrong"
  ],
  "verifier_result": "failed",
  "retrieved_skills": ["table_qa_general_skill"]
}
```

### Output Example

```json
{
  "operations": [
    {
      "op": "SPLIT",
      "target": "table_qa_general_skill",
      "reason": "date normalization is reusable and causes local failures when mixed into general table QA"
    },
    {
      "op": "INSERT",
      "node": {
        "name": "Date Normalization for Table QA",
        "granularity": "atomic",
        "body": "Before filtering by date, inspect date formats, normalize them into a comparable representation, and verify boundary conditions."
      }
    },
    {
      "op": "LINK",
      "source": "table_qa_general_skill",
      "target": "date_normalization_table_qa",
      "type": "depends_on"
    }
  ]
}
```

### Training Strategy

The first version does not need heavy RL. A practical version can use propose-then-verify:

```text
candidate graph operation
-> replay / validation tasks
-> accept if it improves or preserves success
   while reducing token cost or negative transfer
```

## Validation-Time Input and Output

### Input Example

```json
{
  "candidate_operation": {
    "op": "SPLIT",
    "target": "data_analysis_skill",
    "children": ["data_cleaning", "plot_generation", "statistical_reasoning"]
  },
  "validation_tasks": ["task_031", "task_044", "task_052"]
}
```

### Output Example

```json
{
  "decision": "accept",
  "before": {
    "success_rate": 0.62,
    "avg_tokens": 6200,
    "negative_transfer": 0.18
  },
  "after": {
    "success_rate": 0.68,
    "avg_tokens": 3900,
    "negative_transfer": 0.09
  },
  "accepted_ops": ["SPLIT", "LINK"]
}
```

## Test-Time Input and Output

### Input Example

```json
{
  "task": "Analyze a CSV file and generate a plot showing monthly sales trends.",
  "available_skill_graph": "SkillOS graph at time t"
}
```

### Routing Output

```json
{
  "activated_subgraph": {
    "nodes": [
      "load_csv",
      "infer_schema",
      "date_normalization",
      "monthly_aggregation",
      "line_plot_generation"
    ],
    "edges": [
      ["load_csv", "infer_schema", "depends_on"],
      ["date_normalization", "monthly_aggregation", "depends_on"],
      ["monthly_aggregation", "line_plot_generation", "depends_on"]
    ]
  },
  "excluded_skills": [
    "statistical_hypothesis_testing",
    "interactive_dashboard_generation"
  ]
}
```

### Executor Input

```text
User task
+ minimal skill subgraph
+ required examples
+ tool constraints
```

## Ablation Study

### 1. w/o Graph Routing

Replace dependency-aware routing with flat BM25 or embedding retrieval.

Expected result: lower routing precision, higher loaded token cost, and more negative transfer.

### 2. w/o Split

Allow insert, update, and merge, but do not allow large skills to be split into smaller skill nodes.

Expected result: skill documents continue to grow, token cost increases, and heterogeneous tasks suffer.

### 3. w/o Lifecycle Validation

Apply skill operations directly without replay or verifier-gated validation.

Expected result: more unstable long-horizon performance and more harmful skill updates.

### 4. w/o Governance Graph

Keep trace graph and capability graph, but remove high-level split, merge, retire, and routing rules.

Expected result: weaker long-horizon stability and less interpretable governance behavior.

### 5. Full Skill Loading

Load all retrieved or related skills instead of activating a minimal skill subgraph.

Expected result: similar or slightly better short-term success in some cases, but much higher token cost and more negative transfer.

### 6. Flat Skill Bank

Maintain multiple skill documents but remove dependency, conflict, and composition edges.

Expected result: better than monolithic skills, but worse than graph-governed SkillOS.

## Expected Findings

1. **Monolithic skill merge improves reuse but increases token cost and negative transfer.**

2. **Splitting large skills into modular nodes improves robustness on heterogeneous task streams.**

3. **Dependency-aware routing achieves similar or better success with fewer loaded tokens.**

4. **Governance operations become more useful after the skill bank reaches medium size.**

   When there are only a few skills, graph governance may provide limited benefit. As the skill system grows, SkillOS should show stronger advantages.

5. **SPLIT contributes more than MERGE.**

   Prior systems already study merge, prune, and delete. The missing operation is refactor-style split.

6. **Governance graph improves long-horizon stability.**

   The system is less likely to be polluted by harmful or over-generalized skills.

## Main Experiments

## Benchmarks

Recommended benchmarks:

```text
WikiTQ / table QA
data analysis tasks
web / tool-use tasks
OOD task streams
```

## Baselines

```text
No Skill
Trace2Skill original
Trace2Skill + flat multi-skill bank
Trace2Skill + pruning only
SkillBrew-style curation
SkillOS full
```

## Metrics

```text
Task Success Rate
Average Token Cost
Loaded Skill Count
Negative Transfer Rate
OOD Transfer Gain
Skill Bank Size
Redundancy Score
Graph Routing Precision
```

## Expected Main Result

| Method | Success ↑ | Token Cost ↓ | Neg. Transfer ↓ | OOD Gain ↑ |
|---|---:|---:|---:|---:|
| No Skill | Low | Low | Low | Low |
| Trace2Skill | High | High | Medium-High | Medium |
| Flat Skill Bank | High | Medium | Medium | Medium |
| Pruning-only | Medium-High | Medium | Medium | Medium |
| SkillOS | Highest | Low-Medium | Lowest | Highest |

## Main Punchline

> SkillOS does not simply store more skills; it learns to load less, compose better, and transfer more safely.

Alternative paper-style version:

> Modular skill governance yields better long-horizon skill evolution than monolithic skill accumulation.

