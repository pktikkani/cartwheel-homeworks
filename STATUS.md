# STATUS — Cartwheel — 2026-09-24

## Now

- HW1 and HW2 task work is complete. Start HW3 by reading `homework/module-1/hw3.md` and `scenarios/skill/SKILL.md`; follow its human review points.
- Student will record the HW2 video later. Do not treat that deferred submission artifact as a blocker to starting HW3.
- Keep responses short and guide the student through the homework at their chosen pace.

## State

- HW2 Parts A–F and `hw2-traces.json` are committed as `ca0fff7` on `hw2-observability`. Branch is one commit ahead of `origin/main` and has not been pushed.
- Five live requests were inspected in Langfuse Cloud. Part F baseline and revised prompt hashes were verified on root spans; original prompt restored.
- Offline checks: HW2 focused 1 passed, authentication tests 2 passed, full suite 136 passed / 13 skipped / 21 xfailed / 9 xpassed. Live model requests succeeded.
- Langfuse v4 migration was canceled and reverted; SDK 3.15.0 remains. No HW3 work has started.

## Decisions this session

- Student is focused on homework task work and will record submission videos later.
- HW3 coding estimate is 0–1 hour; HW4 review interface coding estimate is 2–4 hours. These are estimates, not handout requirements.

## Gotchas

- Do not restart the canceled Langfuse v4 migration without a new request.
- Preserve `.env`, database, `hw1-session.jsonl`, and unrelated untracked `.idea/`, `HANDOFF.md`, and `docs/`.
- HW3 requires separate scenario generation and application execution, plus student review at the handout's checkpoints.

## Pointers

- HW3 handout: `homework/module-1/hw3.md`; scenario skill: `scenarios/skill/SKILL.md`; HW4 handout: `homework/module-2/hw4.md`.
- HW2 trace details and Cloud permalinks: `hw2-traces.json`. Prompt comparison roots: baseline `6f26061e9e1d387c328f18210093d3dc` (`4b79cf6be56b`); revised `02721e16dc2118b1dfb92c09785433ca` (`db5a8b0ba87d`).

## Handoff

- **Re-entry (2026-09-27):** The nine required HW3 files reached `origin/main` in commits through `6fa9daf`; this handoff is committed separately on top. The `hw3-scenarios` branch remains. Unrelated untracked files remain untouched.
- **HW3 state:** Pilot: 30/30 live runs, 10 student reviews, five valid confirmed failures. Final: 250/250 `gpt-5.5` runs completed (175 coverage, 75 challenge); 15 student reviews (11 accept, four revise). `scenarios/monitoring_scenarios.jsonl` has 50 exact final cases. Offline validators passed. `traces/support_traces.json` has 276 traces covering 250 unique IDs; three inspected traces contain conversation, model, tools, and scenario ID. `reports/smoke-output.txt` exists. Original `data/cartwheel.db` was unchanged; final run used `scenarios/results/hw3-final-DydOFU/`.
- **Next 1:** Student records the <=5-minute HW3 video: show a confirmed pilot failure with evidence, a revised final scenario, one complete final trace, and `jq '[.traces[].cartwheel_scenario_id] | unique | length' traces/support_traces.json` returning 250. The repo portion of HW3 is complete.
- **Next 2:** If starting HW4, read `homework/module-2/hw4.md` and the required error-discovery skill before analysis. Keep quota-error traces separate from agent failures; eight smoke-report error observations came from temporary OpenAI credit exhaustion, while all final result records are completed. Do not create a failure taxonomy as HW3 work.
- **Upstream:** Fetched remote `ai-evals-course/cartwheel-homeworks` `main` at `f515b5b` (2026-09-26); its `homework/README.md` lists seven released assignments, HW1–HW7. This upstream commit was not merged into local `main`.
- **Environment and preservation:** Uvicorn 8010 is stopped; local Langfuse Compose remains running. Credentials stay in `.env`; never print them. Preserve the isolated scratch world and unrelated untracked `.idea/`, `HANDOFF.md`, `docs/`, `scenarios/dimension_plan.md`, `scenarios/pilot_run_review.md`, `scenarios/pilot_sample.md`, and `scenarios/support_scenarios.md`. Daybook fallback is `/Users/pavan/Documents/daily-automation/daily-daybook/2026-09.md` because no Obsidian vault `Projects/*/repo` symlink resolves to this repo.
