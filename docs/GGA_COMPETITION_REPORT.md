# Generalist Gaming Agent (Kaggle) — Feasibility & Work Report

**Date:** 2026-11-28
**Status:** Research and planning only. **No implementation has been started** (per instruction: report first, act later).
**Sources:** Kaggle competition [Overview](https://www.kaggle.com/competitions/generalist-gaming-agent/overview), [Data](https://www.kaggle.com/competitions/generalist-gaming-agent/data), [Rules](https://www.kaggle.com/competitions/generalist-gaming-agent/rules), [Code](https://www.kaggle.com/competitions/generalist-gaming-agent/code) tabs (read 2026-11-28), plus local repo audit.

---

## 1. Executive verdict

| Question | Answer |
| --- | --- |
| Can I enter with my own GGUF models? | **Yes.** The rules explicitly allow attaching model weights/wheels to the notebook and serving them locally with "vLLM, llama.cpp, …". An RTX Pro 6000 (96 GB) is provided. |
| Will LilTii v0.2 / v0.3 work as-is? | **No.** They are companion-chat models trained on Banglish emotion tags, not screen-to-action controllers. Their output contract is incompatible with the required tool-call format. |
| Do I have any assets that genuinely fit? | **Yes, three:** (1) `liltii-v0.3-q4_k_m.gguf` + `liltii-v0.3-mmproj.gguf` (multimodal, small, fast); (2) the hybrid "behavior tree + SLM brain" design in `PUBG_Ally/`; (3) the existing Unsloth/GGUF training pipeline. |
| What is the main risk? | Overfitting to the 4 public games and failing on the 28 hidden games. Generalization, not raw model size, is the competition. |
| Should I start coding? | Not yet — this report is the gate. When you start, begin with the notebook skeleton + reflex baseline (Phase 0–2), **not** the fine-tune. |

**One-sentence strategy:** Use the `PUBG_Ally` hybrid pattern — a fast, deterministic reflex policy running the 200 ms decision loop, with the multimodal v0.3 model as a *slow brain* that emits cached action programs via the competition's `sequence` tool — and only fine-tune after a baseline is measured.

---

## 2. Competition facts (verified)

### 2.1 Task and format

| Item | Detail |
| --- | --- |
| Host | GARC (Generalist Agent Research Collective) — Research Code Competition |
| Task | One offline agent plays **32 browser games across 10 genres**, 10 minutes of game time each |
| Public material | **4 sample games** with `game_id`, `title`, `genre` visible |
| Hidden material | **28 games**, never distributed; agent sees only pixels + a brief of goal and controls |
| Interface | Raw screen frames in, mouse/keyboard actions out; game does **not** pause while the agent thinks |
| Stated goal | Advance agents that learn a game while playing, balance fast action with planning, and do not pause the game to think |

### 2.2 Observation (`gga.protocol.Observation`)

- `obs.image` — JPEG of current frame at the game's viewport size; **its pixels are the action coordinates**.
- `obs.frames` — frames since the previous decision point.
- `obs.history` — up to 8 full-size earlier frames since the previous observation (evenly spread when more).
- `obs.info` — `description`, `controls`, `remaining_s`, `width`, `height`.
- `obs.last_action` — how the previous reply went, including the reason if it was refused.
- `obs.elapsed_s` — drops back near 0 when a new game begins → reset per-game state.
- `gga/protocol.py` is the authoritative field documentation.

### 2.3 Action space — 11 tools

| Tool | Effect |
| --- | --- |
| `click`, `move`, `drag`, `scroll` | Mouse at `(x, y)` |
| `press_key`, `hold_keys`, `key_down`, `key_up` | Keyboard; printable characters or names like `ArrowLeft`, `Space`, `Enter` (`gga.protocol.NAMED_KEYS`) |
| `wait` | Replace running inputs, then idle for `duration_ms` |
| `sequence` | Timed program of **up to 200 steps that runs while the model thinks** |
| `skip` | Change nothing — lets currently running inputs play on |

A refused action changes nothing; the reason arrives in the next `obs.last_action`. Tool JSON schemas are bounded to the viewport and passed in `tools`.

### 2.4 Timing

- Game runs at **20 fps**, decision point every **4 frames = 200 ms**.
- A reply takes effect at the first decision point after arrival; a slow reply lands later but is **never dropped**.
- Every reply except `skip` replaces what is left of the running inputs (a cut-short `press_key` hold is released).
- Each decision must return within **90 s**, or that game ends with its best score so far.
- Exception or unusable reply → `skip` (so a safe fallback is built into the harness).

**Implication:** sub-second replies are a competitive advantage, not a hard requirement. A 0.8B GGUF is easily fast enough. The 200 ms cadence is why the reflex layer matters.

### 2.5 Scoring and leaderboard

- Each game's native progress measure is mapped to `[0, 1]` between a "doing nothing" floor and a human baseline; scores are capped at 1.
- Every submission plays all 32 games. **Public LB = mean of 16 games** (includes the 4 samples). **Private LB = mean of the other 16** and decides final ranking.
- Up to **two final submissions**; final rank uses the better private score.
- Games are deterministic; variation comes only from the agent. Sampling or variable reply timing causes ~0.001–0.01 run-to-run drift. **Deterministic agents score repeatably** — use temperature 0 / fixed seeds when measuring.

### 2.6 Submission mechanics

- Notebook-only competition. The notebook writes `/kaggle/working/agent.py`:
  ```python
  from gga.protocol import Action, Observation, ToolSpec

  class Agent:
      def __init__(self):
          ...  # load model here (runs once, before game 1)

      def step(self, obs: Observation, tools: list[ToolSpec]) -> Action:
          return Action(tool="click", params={"x": 320, "y": 240})
  ```
- **One instance plays all 32 games back to back** — reset per-game state when `obs.elapsed_s` drops near 0.
- Startup budget (installs, model server, `Agent.__init__`): **15 minutes**. Notebook runtime: **9 hours** (CPU or GPU). **Internet disabled.**
- Attach the competition dataset plus any model weights or wheels needed. Freely/publicly available external data including pretrained models is allowed.
- Start a localhost model server in the background if used (vLLM, llama.cpp, …) — counts toward startup.
- Serve unconditionally in the last cell:
  ```python
  from kaggle_evaluation.gga.gga_inference_server import GGAInferenceServer
  server = GGAInferenceServer()
  server.run()
  ```
  If you guard with `KAGGLE_IS_COMPETITION_RERUN`, call `server.run_local_gateway()` in the other branch.
- "Save & Run All" → Submit → **~6 hours** before the score appears (Kaggle reruns all 32 games).
- Local testing (no score): `pip install playwright==1.60.0 pillow`, `playwright install chromium`, then from dataset root:
  `GGA_HEADLESS=1 python -m gga.game --game off_line --agent path/to/agent.py --minutes 1`

### 2.7 Provided dataset files

| Path | Contents |
| --- | --- |
| `gga/` | Harness — `gga.protocol` (agent interface), `gga.game` (local play) |
| `kaggle_evaluation/` | `GGAInferenceServer` for submissions |
| `assets/` | The four sample games |
| `kit/` | Offline installs: Playwright + Chromium + system packages, and compressed-tensors for 4-bit weights |

### 2.8 Timeline, prizes, rules

- Start: **Nov 23, 2026**. Entry + team merger deadline: **Feb 22, 2027**. Final submission: **Mar 1, 2027**. ~3 months remain.
- Prizes: $16k / $12k / $9k / $7k / $6k (total $50k). ~1,992 entrants, 588 teams at time of check.
- Notable rules: no hand-labeling/human prediction of validation or test records; no private code sharing outside teams; submission code must be licensed under an OSI license that does not limit commercial use (**exemptions exist for pretrained models with incompatible licenses and commercially available software**); an ineligible/prize-restricted country blocks prize eligibility, not participation (check local rules).
- Reference citation: Benedikt Schink, Matin Urdu, Arian Urdu, Wayne Chi, Stephanie Milani, Chengshuai Shi, Martyna Plomecka, Yao Yan, Fei Fang, Chi Jin, Karthik Narasimhan, Kiran Vodrahalli, Seth Karten, Ashley Oldacre. *Generalist Gaming Agent*, Kaggle, 2026.

---

## 3. Audit of local assets

| Asset | Role in this competition | Verdict |
| --- | --- | --- |
| `app/src/main/assets/models/liltii-v0.2-v3-q4_0.gguf` (Qwen2.5-0.5B, text-only, Banglish + emotion tags) | Needs pixels | ❌ Not usable as the agent brain |
| `PUBG_Ally/models/bangla-smollm-135m-v3-q4_0.gguf` | Text-only, 135M | ❌ Too weak; at most a fallback text classifier |
| `app/src/main/assets/models/liltii-v0.3-q4_k_m.gguf` (522 MB) + `liltii-v0.3-mmproj.gguf` (196 MB) | Qwen3.5-0.8B multimodal + vision projector, released to HF as `Lilti_kiraa-v0.3-Qwen3.5-0.8B` | ✅ **Primary candidate** — correct modality and speed |
| `training/archive_v03_assets/v0.3/liltii-v0.3-gguf_gguf/Qwen3.5-0.8B.{Q8_0,Q4_K_M,F16-mmproj}.gguf` | Base weights/projector for a new fine-tune | ✅ Useful as fine-tune base |
| `app/src/main/java/com/cupcake/ai/EmotionGrammar.kt` (`TAG_ACTION`) | Forces `[emo: tag] *action* reply` | ❌ Must be replaced by a tool-call grammar (GBNF or JSON schema) |
| `PUBG_Ally/pubg_ally_agent.py` (`BehaviorTree` + `SLMBrain`) | Reflexes + slow tactical brain | ✅ **Architecture blueprint** — directly matches the competition's stated goal |
| `app/src/main/cpp/third_party/llama.cpp` JNI bridge | Android-side AI boundary | ⚠️ Not reusable inside a Python notebook; use `llama-server`/`llama-cpp-python` instead. **Do not modify the submodule.** |
| `training/train_unsloth_v03.py`, `training/kaggle/*.ipynb`, ChatML JSONL datasets | Reusable recipe for action-trajectory fine-tuning | ✅ Reusable after dataset swap |
| `HpBarReader.kt`, `HpEventGate.kt`, ML Kit OCR plan | Android/Kotlin pixel heuristics | ⚠️ Not portable as-is; the *pixel-diff gate idea* is portable |
| Compose UI, Hilt, Room, BLE, ESP32 firmware, WebSocket, billing, `EnergyManager`, 15 mini-games, ESP faces | Companion-app concerns | ❌ Irrelevant — do not port |
| AGENTS.md rule: "games always stay on-device, LOCAL_LLAMA only, never cloud" | Project policy | ✅ Aligns naturally with the offline competition |

**Doc drift to note:** `AGENTS.md` still describes v0.3 as the "next model" and Qwen3.5-0.8B as "future", while `SESSIONS.md` (2026-11-24) and the HF release confirm v0.3 was already trained on Qwen3.5-0.8B with an mmproj. Trust `SESSIONS.md` / HF card; update `AGENTS.md` when you next touch it.

---

## 4. Gap analysis — needed vs. not needed

### 4.1 What IS needed

1. **Admin:** Kaggle account, accept rules before Feb 22 2027, join the competition, attach the competition dataset.
2. **Notebook skeleton:** attach `liltii-v0.3-q4_k_m.gguf` + `liltii-v0.3-mmproj.gguf` (and any wheel), start `llama-server` in the background on localhost within 15 min, `%%writefile /kaggle/working/agent.py`, end with `GGAInferenceServer().run()`.
3. **`Agent` implementation:** `__init__` (load model once) and `step(obs, tools) -> Action`; detect a new game from `obs.elapsed_s` and clear per-game state/memory.
4. **Action contract:** parse `tools` JSON schemas, emit only valid tool names and in-bounds coordinates; handle refusals via `obs.last_action`; guarantee a valid fallback so exceptions become `skip`.
5. **Fast reflex layer:** deterministic heuristics/behavior tree keyed on `obs.info.description`/`controls` plus cheap frame features; drive the 200 ms loop with `click`/`press_key`/`hold_keys`; publish multi-step plans through `sequence` and yield with `skip` while the model computes.
6. **Vision path:** downscale `obs.image` before the mmproj encoder, use the correct llama.cpp multimodal chat template, and keep the image→token cost bounded so a decision stays well under 90 s.
7. **Trajectory dataset:** run the four sample games locally with `gga.game`, record `(frame + brief + recent history) → tool call` pairs, including exploration and recovery from refusals. This is the only game data you are allowed to train on.
8. **Fine-tune (only after a baseline exists):** LoRA on Qwen3.5-0.8B with loss on action tokens only; export GGUF; A/B against the non-fine-tuned model and against the decision-model starter notebook.
9. **Robustness & repeatability:** temperature 0 / fixed seeds for scoring runs; hard latency budget; watch `obs.info.remaining_s`; gracefully reset at game boundaries; prepare two final submissions.
10. **Licensing:** set an OSI license on submission code; verify the Qwen3.5 and fine-tuned model licenses; keep any pretrained-model license mismatch documented for the exemption clause.
11. **Local eval loop:** 1-minute smoke tests → longer runs on all 4 sample games → track per-game normalized progress; never judge on a single lucky run.

### 4.2 What is NOT needed (leave it out)

- Android app, Compose/Material3 UI, Hilt/KAPT, Room, navigation, themes.
- ESP32 firmware, BLE/GATT, WebSocket, sensor pipelines, motor/face frames, gesture detection.
- Billing/freemium, `EnergyManager`, points/XP, achievements, character cards, chat history persistence.
- Emotion tags and `[mode: …]` personality tags — actively harmful here; the output must be tool calls.
- Cloud / Ollama / OpenAI-compatible providers — internet is disabled and the task is offline by design.
- ML Kit OCR and pixel readers **if** the mmproj path works (keep the idea, drop the Android code).
- The 15 in-app mini-games and their Q-learning bots — different environment, different action space.
- Any modification to `app/src/main/cpp/third_party/llama.cpp/` (git submodule).
- Committing GGUF files to git — attach them to the Kaggle notebook/dataset instead (they are gitignored for good reason).

---

## 5. Recommended architecture

```
                     every 200 ms (game never pauses)
 obs.image / frames ───────────────► ┌──────────────────────────┐
 obs.info brief     ───────────────► │ FAST REFLEX POLICY       │
 obs.last_action    ───────────────► │ heuristics + behavior    │  ──► click / press_key /
                                    │ tree, deterministic      │      hold_keys / drag / wait
                                    └──────────────────────────┘
                                                 │ every ~1–2 s or on novelty
                                                 ▼
                                    ┌──────────────────────────┐
                                    │ SLOW BRAIN (v0.3 mmproj) │
                                    │ frame + brief → plan     │  ──► sequence (≤200 steps)
                                    │ tool-call grammar        │      cached & replayed via skip
                                    └──────────────────────────┘
                                                 │
                              fallback ladder: SLM → heuristic → skip
                              reset all state when obs.elapsed_s → ~0
```

Key design decisions:

- **Reflexes own the clock.** The 200 ms loop never waits on the model; `skip` lets a running `sequence` play out during inference.
- **The model is a planner, not a joystick.** It emits short action programs, not per-frame twitches — this is what `sequence` was built for.
- **The brief is the main generalization lever.** `obs.info.description` and `controls` are the only semantic ground truth for all 28 hidden games; parse them into an action vocabulary every game.
- **Determinism by default.** Fixed sampling and stable reply timing make local measurements trustworthy and remove the 0.001–0.01 drift.
- **Never trust an unparsed reply.** Validate every action against `tools`; on any error, `skip`.

---

## 6. Work breakdown (proposed backlog items)

| Phase | ID | Work | Exit criterion |
| --- | --- | --- | --- |
| 0 — Admin | GGA-00 | Join comp, accept rules, attach dataset + GGUFs, verify local sample game runs headless | `gga.game` plays `off_line` for 1 min with a stub agent |
| 1 — Skeleton | GGA-01 | Notebook boots `llama-server` with mmproj; `agent.py` returns valid `skip`/`click`; end cell starts `GGAInferenceServer` | Notebook saves & runs all; submission accepted; placeholder score |
| 2 — Reflex baseline | GGA-02 | Brief parser + heuristic policy using the 11 tools; `sequence`/`skip` orchestration | Nonzero score on all 4 sample games |
| 3 — Vision integration | GGA-03 | Multimodal inference on `obs.image`, tool-call grammar, latency budget check | SLM-produced actions validate and land within ~1 s |
| 4 — Trajectory fine-tune | GGA-04 | Collect trajectories, LoRA fine-tune, GGUF export, A/B | Fine-tuned ≥ baseline on held-out sample game |
| 5 — Generalization | GGA-05 | Prompt/action randomization, refusal recovery, game-boundary reset, seed stability | Repeatable scores; no crashes across full 32-game rerun |
| 6 — Final | GGA-06 | Select two final submissions before Mar 1 2027 | Both complete rerun; better private score chosen |

**Do phases 0–2 before spending GPU time on phase 4.** The competition offers a decision-model starter notebook that may beat a 0.5B/0.8B LLM on score; measure it before committing to the LLM path.

---

## 7. Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Overfitting to the 4 public games | Main failure mode on the private 16 | Train on *principles* from the brief, not game IDs; randomize action distributions; keep heuristics genre-agnostic |
| 0.8B model misreads frames (ScreenSpot Pro ≈46.5 for this class of model) | Bad action choices | Downscale/crop to HUD and relevant regions; keep reflex fallback; never let the model be the only controller |
| ~6 h scoring feedback loop | Slow iteration | Use local `gga.game` for all iteration; submit only meaningful checkpoints; keep logs per game |
| Run-to-run drift from sampling | Misleading comparisons | temperature 0, fixed seeds, fixed reply delay |
| 90 s decision timeout / 9 h notebook limit | Game ends early / run fails | Hard per-decision timer; cap generated tokens; `skip` on timeout; smoke-test full-length runs locally |
| License mismatch or missing OSI license | Disqualification of a winning submission | Check Qwen3.5 license now; put a license file in the submission notebook; document the pretrained-model exemption |
| Concurrency with other repo work | Lost changes | Commit only report/docs; leave unrelated uncommitted work untouched |

---

## 8. Decision gate

- **Go / no-go for using your models:** Go — but as a *multimodal slow brain*, not as a drop-in replacement for the starter agent.
- **First action when you start:** Phase 0 + 1 (notebook skeleton, attach weights, verify one local game). This de-risks the whole competition in a day.
- **Second action:** Phase 2 reflex baseline. If the decision-model starter already scores competitively, consider switching the "brain" to a small policy network and keep the LLM only for brief interpretation.
- **Do not** spend the first week fine-tuning LilTii on chat-style emotion-tag data — that data has zero overlap with the action contract.

---

## 9. Reference links

- Competition: https://www.kaggle.com/competitions/generalist-gaming-agent
- Overview: https://www.kaggle.com/competitions/generalist-gaming-agent/overview
- Data: https://www.kaggle.com/competitions/generalist-gaming-agent/data
- Code: https://www.kaggle.com/competitions/generalist-gaming-agent/code
- Rules: https://www.kaggle.com/competitions/generalist-gaming-agent/rules
- Local blueprint: `PUBG_Ally/README.md`, `PUBG_Ally/pubg_ally_agent.py`
- Local model card context: `SESSIONS.md` (2026-11-24), HF `bayazidhs04/Lilti_kiraa-v0.3-Qwen3.5-0.8B`
