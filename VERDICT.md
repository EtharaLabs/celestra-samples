# VERDICT

CRUCIBLE report for run `crucible-mumukshu-panchal-ethara-ai-20261030t000000z-audit`, audit of the sealed task bundle staged under `/Users/apple/Sources/office/celestra-samples`: `deb80ee4-8751-59a2-8392-0a81748ffb38` (PyPSA multi-period optimisation under linopy v1 snapshot semantics, author `mumukshu.panchal`, upstream PyPSA PR 1829, base `6d1da8049b33`, reference `4f374fbd77ae`), with one author-side Claude Opus 5 rollout, 2026-10-30.

## Executive summary

- ✅ The grader partitions cleanly and is reproducible: `solution/recompute.py` regenerates `solve.sh`, `TRUTH.md`, `provenance.yaml`, `test_output.py`, `config.json`, `judge.toml`, and `reference.diff` byte-identically from `grounding.yaml`, and the sealed-test and `reference_diff_sha256` digests verify. C1–C4 + B1 split the 203 fail-to-pass nodes disjointly, and K1 holds the 221 pass-to-pass nodes with no overlap.
- ✅ The recorded reward recomputes exactly from the rollout's own `graded.json`: 157/203 F2P pass (R1 0.7734), 221/221 P2P pass, C4/B1/P1/A1 pass, C1/C2/C3 fail, so `(5 + 5×0.7734 + 3 + 5 + 3 + 3 + 1)/34 = 0.702`.
- 🟡 The shipped verifier records did not come from the shipped `score.py`/`test.sh`. `reward-details.json` is Reward Kit's raw group output without the `compiled`/`judged` envelope that `score.py` writes, and `test-stdout.txt` reads `reward: 0.702`, which `test.sh` never prints. The judged path's status is therefore unrecorded (G-VERIFIER-RECORD).
- 🟡 The rollout harness does not match the image. `openhands_sdk.txt` reports OpenHands SDK v1.58.2, but `agent-requirements.txt` pins `openhands-sdk==1.27.0`, and `environment/Dockerfile` builds `/opt/openhands-sdk-venv` and then removes it with `RUN rm -rf`, contradicting its own comment that Harbor "finds /opt/openhands-sdk-venv ready" (G-AGENT-HARNESS).
- 🟡 `policy.yaml` says "no-network baseline for agent and verifier" and "no credential … reaches the trial", but `task.toml` gives the verifier an `api.anthropic.com` allowlist and passes `ANTHROPIC_API_KEY`/`CLAUDE_CODE_OAUTH_TOKEN` through `[verifier.env]` for the judge (G-POLICY-DRIFT).
- 🟢 The FORGE canaries are initialized and consistent, but the attestation digests read `attestation-unavailable` and `screening_roots` is unresolved. A `.DS_Store` ships inside the rollout directory (G-ATTEST, G-HYGIENE).
- Gate summary: the task bytes, statement, and grader are sound and discriminating. The open items are a mis-packaged trajectory, verifier records that predate the shipped scorer, harness/policy drift, and the lack of a counted oracle pilot. All are fixable without reworking the task.

## Disposition

HOLD

## Findings

### Grader discrimination (class 19)

- ✅ G-PARTITION, acknowledged clean (`deb80ee4`): The gate (`none_pass` over 203 F2P nodes) zeroes any submission that fixes nothing. C1 (S1 minus `test_model_snapshot_index_invalid_option`, 39), C2 (S2, 140), C3 (S3, 16), C4 (S4, 7), and B1 (the invalid-option node, 1) union to exactly the 203 F2P nodes with no overlap. K1 is `any_fail` over the 221 S5 P2P nodes, disjoint from the F2P set. The two deselected piecewise nodes are documented (they fail under the reference itself, an upstream PR 1829 defect) and appear in no item.
- ✅ G-ROUTES, acknowledged clean (`deb80ee4`): `TRUTH.md` names three wrong-answer routes, each rejected by graded nodes: global-roll (4 nodes, cyclic state across periods), unweighted-periods (9, objective/limit weighting), and single-start (10, per-period resets). The rollout shows the binary coverage items biting: a 77% F2P pass rate still scored C1/C2/C3 at 0.
- ✅ G-ANTI-STEER, acknowledged clean (`deb80ee4`): `run_graded.py` overlays only `pypsa/`, refuses `conftest.py`, `sitecustomize.py`, `usercustomize.py`, and `.pth`, and resolves duplicate outcome lines to the worst one. Tests run as uid 10001 with `PYTHON*`/`PYTEST*` stripped. The rollout's `test/conftest.py` edit was correctly ignored (`steering: []`).

### Statement and grader integrity (class 18)

- ✅ G-STMT-RECONCILE, acknowledged clean (`deb80ee4`): Every graded item maps to an instruction rule: the option values and `ValueError` → S1/B1; flat labels, auxiliary coordinates, and `da`/`parameters.snapshots`/`extra_functionality` consistency → S1/J1; per-period storage, ramps, limits, and weighting → S1/S4; expressions ↔ statistics → S2/S3; preserved names, groupings, and log strings → S5/K1/J2; option documentation → A1 via the `options_describe` probe.
- 🟡 G-VERIFIER-RECORD, retained (`deb80ee4`): `score.py` always writes `{"reward", "compiled", …}` and, when judged items exist, a `judged` status (`not run` / `skipped` / `run` / `failed`). The shipped `reward-details.json` has neither field, and `test-stdout.txt` holds a line no shipped script emits. Whether J1/J2 ran is unrecorded. They can only lower the 0.702 (`compiled × (34 + 6 × judged)/40`), but the record should come from the shipped scorer.

### Domain integrity and reward provenance (class 6)

- 🟡 G-AGENT-HARNESS, retained (`deb80ee4`): The SDK version that ran (v1.58.2) is not the pinned one (1.27.0), and the in-image venv the comment depends on is deleted. With `[agent] network_mode = "no-network"`, the agent install path that produced this rollout is not the one the bundle describes. `openhands_sdk.txt` also ends inside a `timeout 900 python -m pytest` call with no finish record.
- ✅ G-REWARD-PROVENANCE, acknowledged clean (`deb80ee4`): 0.702 recomputes from `graded.json` (424 outcomes: 378 PASSED, 46 FAILED; `refused: null`; A1 probe present). The failures fall in `extra_functionality` snapshots (2), expressions/equivalence (39), and statistics (5). `agent.patch` touches 11 `pypsa/` files and leaves out six that the reference changes: `_linopy_compat.py`, `network/abstract.py`, `piecewise.py`, `variables.py`, `window.py`, and `statistics/expressions.py`.
- 🟢 G-ATTEST, retained (`deb80ee4`): The three `FORGE-CANARY-SLOT` values are non-zero and identical across all five `solution/` files and absent from `environment/`, `tests/`, and `trajectories/`, so no leak was observed. Both attestation digests and signers read `attestation-unavailable`, and `screening_roots` is "unresolved: FORGE_VIEW publishes no screening roots".

### Supply-chain and environment build (class 5 / 20)

- 🟡 G-POLICY-DRIFT, retained (`deb80ee4`): The `policy.yaml` `network` and `environment` notes describe a no-network, credential-free verifier. `task.toml` allowlists `api.anthropic.com` and forwards two judge credentials. Bring the policy text into line with the judged design.
- ✅ G-ENV-PIN, acknowledged clean (`deb80ee4`): Every base is digest-pinned: `dockerfile:1.17`, `alpine/git:2.49.1`, and `python:3.12-slim-bookworm@sha256:6a0e06f5…`, the same in both images. All wheels install `--no-index --require-hashes`. `curl` is version-pinned from `snapshot.debian.org/20260818T000000Z`. The source fetch asserts `rev-parse HEAD == 6d1da8049b33` and strips history. The five example networks are `ADD --checksum` pinned. `tests/tools.txt` matches `environment/tools.txt`.
- ✅ G-ISO-STRUCTURE, acknowledged clean (`deb80ee4`): `environment_mode = "separate"`. The agent runs as uid 10001 with no network. The agent image copies neither `tests/` nor `solution/`, and `tests/.dockerignore` allowlists only grader inputs. The verifier starts as root only to `chmod a+rX` the artifact, then grades as uid 10001 via `setpriv`.
- 🟢 G-HYGIENE, retained (`deb80ee4`): `trajectories/opus-5/run_1/.DS_Store` ships in the bundle.

## Coverage gaps

- No oracle rollout or signed external pilot is in the bundle, and `solve.sh` was not executed in this audit. That the reference passes all 203 F2P and 221 P2P nodes is asserted by the grounding, not demonstrated. pass@1 = 0 for the one shipped rollout.
- Image builds, `linux/amd64` + `linux/arm64` buildability, and a `grype`/SBOM scan were not run. The builds also need network access to GitHub and `data.pypsa.org`.
- The judged items J1/J2 were not exercised here, and the shipped record does not show whether they ran. A run without a credential or without `api.anthropic.com` reach scores compiled-only by design.
- The example-network licence chain is `accepted-by-provenance` (named gap `example-network-licence-by-provenance`): the `data.pypsa.org` bytes differ from the in-tree copies.

## Escalations

- Replace `trajectories/opus-5/run_1/agent/trajectory.json` with the PyPSA run's own trajectory, or re-run the rollout. Ship the `reward-details.json` and stdout that the shipped `test.sh` → `score.py` produce, including the `judged` status.
- Reconcile the agent harness: either keep `/opt/openhands-sdk-venv` in the image at the pinned 1.27.0, or update the pin and comment to the SDK that actually runs.
- Update `policy.yaml`'s network and environment notes to the judged-verifier design, and record one counted oracle pilot through `solve.sh` to confirm 1.0.
- Remove the `.DS_Store`, and resolve or explicitly accept the attestation and screening-root gaps.

## Flag legend

- 🔴 retained finding that caps the bundle outcome; 🟡 retained finding to fix or accept; 🟢 low-severity retained finding; ✅ acknowledged clean.
