<p align="center"><img src="images/hero.svg" alt="celestra" width="720"></p>

# Celestra BeyondSWE: samples

<p align="center"><b>Five sample tasks from celestra, a corpus of hard Harbor tasks that reach beyond single-repository bug fixing.</b></p>

<p align="center"><a href="#summary"><img src="https://img.shields.io/badge/samples-5%2F5-845EF7" alt="samples: 5/5"></a> <a href="#summary"><img src="https://img.shields.io/badge/harbor_schema-1.4-845EF7" alt="harbor schema: 1.4"></a> <a href="#trials"><img src="https://img.shields.io/badge/difficulty-unsolved_by_frontier-845EF7" alt="difficulty: unsolved by frontier"></a></p>

<p align="center"><sub><a href="#abstract">Abstract</a> | <a href="#summary">Summary</a> | <a href="#tasks">Tasks</a> | <a href="#trials">Trials</a> | <a href="#coverage">Coverage</a> | <a href="#dataset-structure">Dataset structure</a> | <a href="#reproduction">Reproduction</a> | <a href="#cite">Cite</a> | <a href="#contact">Contact</a></sub></p>

## Abstract

Celestra is a corpus of hard, realistic software-engineering tasks in [Harbor](https://github.com/laude-institute/harbor) format, drawn from real merged changes in open source Python projects. This is based on [BeyondSWE](https://arxiv.org/abs/2603.03194) (arXiv:2603.03194). Every task ships a sandbox image, the instruction the agent reads, a verifier hidden from the agent, and a reference solution. The reward is continuous from 0 to 1: the compiled tests score first, and LLM-judged criteria can only lower that score. A rollout counts as solved only at reward 1.

This repository holds the five-task sample, covering three of BeyondSWE's four settings. One task is a domain-specific issue resolution (DomainFix): the agent fixes how PyBaMM's battery solvers restart after discontinuities and model changes. One is a dependency-driven migration (DepMigrate): the agent moves PyPSA's multi-period optimisation onto linopy's v1 semantics. Three are cross-repository issue resolutions (CrossRepo): a LangChain middleware feature whose fix must land in both the LangChain and the LangGraph checkouts, a Sentry SDK boto3 tracing change that follows botocore's request lifecycle, and a fontTools change that brings the classic AAT `mort` table up to the `morx` object model. Task images hold no upstream version history and agent web search is disabled, so the upstream fix is not reachable from inside the sandbox.

Each sample ships one rollout with `claude-opus-5-5`, scored by the task's own verifier and judged by `gpt-6.1-sol` over 20 trials per criterion. None of the five trials reached reward 1, and the best combined reward was 0.6434, so every task keeps headroom above `claude-opus-5-5`.

## Summary

| Property | Value |
| --- | --- |
| Samples | 5/5 |
| Target Benchmark | BeyondSWE |
| Settings | CrossRepo (3), DepMigrate (1), DomainFix (1) |
| Domains | Battery modelling, energy-system optimisation, agent frameworks, observability, font engineering |
| Language | Python |
| Format | Harbor task, schema 1.4 |
| Platforms | linux/amd64, linux/arm64 |
| Base image | `python:3.12-slim-bookworm`, digest-pinned |
| Reward | Continuous in [0, 1]; compiled tests, lowered only by LLM-judged criteria |
| Agent time limit | 2 to 5 hours per task |
| Agent | OpenHands SDK 1.58.2 with `claude-opus-5-5` |
| Judge | `gpt-6.1-sol`, 20 trials per criterion, majority rule, with calibration controls |
| Trials | 1 per task |
| Solved by `claude-opus-5-5` | 0 of 5 |
| Mean compiled score | 0.5954 |
| Mean combined reward | 0.5199 |
| Judged criteria passed | 14 of 49 |
| Mean trial time | 1h 7m 21s |

## Tasks

| Task | Setting | Project | Objective | Time limit |
| --- | --- | --- | --- | --- |
| [`04312261`](04312261-7c49-5547-aa9c-d00648750582/) | DomainFix | PyBaMM | Make PyBaMM's solvers restart each integration segment from the right state and sensitivities after input-timed discontinuities, periodic resets, and changes of model, and keep continued solves consistent when the requested sensitivities change. | 2 h |
| [`594fe341`](594fe341-7f10-5685-aeb1-ffa86424017d/) | CrossRepo | LangChain + LangGraph | Let LangChain's `HumanInTheLoopMiddleware` review each tool call on its own with a typed answer schema, which needs LangGraph's `interrupt` to carry a response schema and to reject an invalid answer without keeping it; the fix spans both checkouts. | 3 h |
| [`98258d6a`](98258d6a-da32-5d91-b0cd-3d0bab26a467/) | DepMigrate | PyPSA / linopy | Make PyPSA's multi-period optimisation work under linopy's v1 arithmetic semantics, which forbid a MultiIndex dimension coordinate, by building models over a flat snapshot dimension through the model builders, expressions, statistics, and transport delays. | 5 h |
| [`b82b72a4`](b82b72a4-cbcb-5dca-b5f6-be150573e37e/) | CrossRepo | Sentry Python SDK / boto3 | Make the SDK's boto3 integration trace one span per botocore client call, covering every retry attempt, failures before any request exists, and streamed response bodies until they are consumed, in both the static and the span-streaming tracing modes. | 2 h |
| [`e399ed3a`](e399ed3a-ba44-5777-b1bf-7cb0d481d40e/) | CrossRepo | fontTools | Make fontTools decompile, dump to TTX, read from TTX and compile classic AAT `mort` tables with rearrangement, contextual, ligature and insertion subtables, in the classic encoding and the `morx` object model, leaving `morx` and non-contextual `mort` unchanged. | 3 h |

## Trials

Each task was run once with `claude-opus-5-5` on Harbor's `openhands-sdk` agent (OpenHands SDK 1.58.2), and scored by the task's own verifier: the compiled tests inside the verifier image, then the judged criteria over the agent's diff with `gpt-6.1-sol`, 20 trials per criterion, a criterion passing on a majority of trials. Trials are stored under each task's `trials/opus-5-5/<task-uuid>__<trial-id>/`, Harbor's trial layout under the agent model.

| Task | Agent | Compiled score | Judged criteria passed | Combined reward | Graded nodes passed | Trial time |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| [`04312261-7c49-5547-aa9c-d00648750582`](04312261-7c49-5547-aa9c-d00648750582/trials/opus-5-5/) | OpenHands SDK | 0.5962 | 1 / 4 | 0.5653 | 199 / 223 | 1h 4m 50s |
| [`594fe341-7f10-5685-aeb1-ffa86424017d`](594fe341-7f10-5685-aeb1-ffa86424017d/trials/opus-5-5/) | OpenHands SDK | 0.7015 | 3 / 7 | 0.5011 | 720 / 726 | 51m 10s |
| [`98258d6a-da32-5d91-b0cd-3d0bab26a467`](98258d6a-da32-5d91-b0cd-3d0bab26a467/trials/opus-5-5/) | OpenHands SDK | 0.7244 | 5 / 18 | 0.6148 | 879 / 1045 | 2h 56m 5s |
| [`b82b72a4-cbcb-5dca-b5f6-be150573e37e`](b82b72a4-cbcb-5dca-b5f6-be150573e37e/trials/opus-5-5/) | OpenHands SDK | 0.6798 | 2 / 9 | 0.6434 | 157 / 167 | 12m 40s |
| [`e399ed3a-ba44-5777-b1bf-7cb0d481d40e`](e399ed3a-ba44-5777-b1bf-7cb0d481d40e/trials/opus-5-5/) | OpenHands SDK | 0.2750 | 3 / 11 | 0.2750 | 1429 / 1447 | 32m 1s |
| **mean** | | **0.5954** | **14 / 49** | **0.5199** | | **1h 7m 21s** |

The **mean** row averages the scores and trial time over the five trials; its criteria cell is the total across them. Trial time is Harbor's wall time from trial start to verifier finish. The compiled score weighs each required behaviour as an all-or-nothing item, with a regression gate that zeroes the score when any existing test breaks, so a rollout that fixes most of a change still scores well below 1. The combined reward multiplies the compiled score by the share of judged criteria passed, scaled by the task's compiled and judged weights, so the judge only ever lowers it.

Every trial ran under the task's own time limit as delivered in its `task.toml`, with no run-time extension; each agent stopped on its own.

Three rows deserve a reading. `594fe341` is the only task whose fix spans two repositories; the agent found that both checkouts needed changing, edited nine files across them, passed 720 of 726 nodes, and still lost four of seven judged criteria, among them focus and backwards compatibility of the LangGraph change. `e399ed3a` passed 1429 of 1447 graded nodes but scored 0.2750, because the eighteen failing nodes sit across the all-or-nothing items the task is built around. `04312261` passed every regression test and 199 of 223 nodes, but the solver-restart items that carry its weight stayed unfixed.

Each trial folder is Harbor's trial output:

| Path | Contents |
| --- | --- |
| `config.json` | Trial configuration: task, agent, model, environment and verifier settings |
| `result.json` | Agent, model, timings, and the verifier's compiled reward |
| `trial.log` | Harbor's log of the trial |
| `agent.patch` | The agent's final diff, as the verifier graded it |
| `agent/` | Agent trajectory (`trajectory.json`, ATIF 1.7) and the scaffold's own log (`openhands_sdk.txt`) |
| `verifier/reward.txt`, `verifier/reward.json`, `verifier/reward-details.json` | The final combined reward and how it was formed |
| `verifier/reward-compiled.json`, `verifier/reward-details-compiled.json` | The compiled score and its items |
| `verifier/graded.json`, `verifier/ctrf.json`, `verifier/test-stdout.txt` | Per-node test outcomes and test output from the verifier image |
| `verifier/judge-request.json` | The judge request the verifier wrote for stage 2 |
| `verifier/judge/` | `judge-scores.json` (per criterion, 20 trials), `controls.json` (calibration controls against the reference), and every vote under `votes/<case>/<criterion>.<trial>.json` |

## Coverage

| Keyword | Tasks |
| --- | --- |
| aat | 1 |
| battery-modelling | 1 |
| binary-format | 1 |
| boto3 | 1 |
| botocore | 1 |
| cross-repo | 3 |
| depmigrate | 1 |
| domainfix | 1 |
| energy-systems | 1 |
| fonttools | 1 |
| human-in-the-loop | 1 |
| interrupt | 1 |
| langchain | 1 |
| langgraph | 1 |
| linopy | 1 |
| mort | 1 |
| morx | 1 |
| observability | 1 |
| ode-dae | 1 |
| opentype | 1 |
| optimization | 1 |
| pybamm | 1 |
| pypsa | 1 |
| python | 5 |
| sensitivities | 1 |
| sentry-python | 1 |
| tracing | 1 |

## Dataset structure

Each task is one Harbor task in a directory named by its uuid.

| Task | Keywords |
| --- | --- |
| [`04312261-7c49-5547-aa9c-d00648750582`](04312261-7c49-5547-aa9c-d00648750582/) | pybamm, battery-modelling, ode-dae, sensitivities, domainfix, python |
| [`594fe341-7f10-5685-aeb1-ffa86424017d`](594fe341-7f10-5685-aeb1-ffa86424017d/) | langgraph, langchain, human-in-the-loop, interrupt, cross-repo, python |
| [`98258d6a-da32-5d91-b0cd-3d0bab26a467`](98258d6a-da32-5d91-b0cd-3d0bab26a467/) | pypsa, linopy, optimization, energy-systems, depmigrate, python |
| [`b82b72a4-cbcb-5dca-b5f6-be150573e37e`](b82b72a4-cbcb-5dca-b5f6-be150573e37e/) | sentry-python, boto3, botocore, tracing, observability, cross-repo, python |
| [`e399ed3a-ba44-5777-b1bf-7cb0d481d40e`](e399ed3a-ba44-5777-b1bf-7cb0d481d40e/) | fonttools, aat, mort, morx, opentype, binary-format, crossrepo, python |

```
<uuid>/
├── task.toml         runner manifest
├── instruction.md    objective the agent reads
├── environment/      sandbox image, with the target repository at its base commit
├── tests/            verifier, hidden from the agent (graded tests, judge rubric, reference diff)
├── solution/         reference solution
└── trials/
    └── opus-5-5/                      trials with claude-opus-5-5
        └── <task-uuid>__<trial-id>/   one scored rollout
            ├── config.json
            ├── result.json
            ├── trial.log
            ├── agent/        trajectory.json and the scaffold's log
            └── verifier/     reward.txt, test output, grading details, judge votes
```

## Reproduction

Each task directory is a complete Harbor task: `task.toml` is the runner manifest, `instruction.md` the objective, `environment/` the sandbox image (the target repository, or both repositories for the cross-checkout task, installed in editable mode at the base commit with a hash-locked dependency set), `tests/` the verifier, and `solution/` the reference solution. The trials above were produced with:

```bash
harbor run -p <task-dir> -a openhands-sdk -m anthropic/claude-opus-5-5
```

Run `harbor run -p <task-dir> -a oracle` to score a task's reference solution; every oracle scores 1 and every untouched environment (`-a nop`) scores 0.

The verifier scores the compiled tests inside its own image and writes `judge-request.json`; the judged criteria are then scored outside the verifier with the model `tests/judge/stages.json` names, and `tests/combine.py` folds them into the final reward.

## Cite

A citation for celestra will be published here once it releases its first full dataset. The grounding benchmark it builds on is BeyondSWE.

```bibtex
@misc{beyondswe2026,
  title        = {BeyondSWE: Can Current Code Agent Survive Beyond Single-Repo Bug Fixing?},
  author       = {Chen, Guoxin and others},
  year         = {2026},
  eprint       = {2603.03194},
  archivePrefix= {arXiv},
  url          = {https://arxiv.org/abs/2603.03194}
}
```

## Contact

Celestra is built by [Ethara.AI](https://github.com/Ethara-Ai).

For questions about the benchmarking dataset, contact research@ethara.ai.

Copyright (c) 2026 Green Rider Technology LLP (Ethara AI). All rights reserved.
