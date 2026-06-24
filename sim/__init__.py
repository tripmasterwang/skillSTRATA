"""Deterministic simulation harness for SkillOS experiments.

The simulator models the *mechanism* the proposal argues about — skill bloat raises token
cost and negative transfer; precise routing loads fewer, more relevant skills — so the main
table and all six ablations reproduce in seconds with a fixed ``--seed`` and no API budget.

See ``simulator.py`` for the documented seam to swap in Trace2Skill's real agent + verifier.
"""
