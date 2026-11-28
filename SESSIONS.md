# SESSIONS.md — CupCake Session Log

> Running notes, decisions, bugs, and pending items between coding sessions.
> AI agents: append a dated entry after every session. Humans: scan for context.

---

## Session Template
```
### YYYY-MM-DD — [Session goal]
**Done:** ...
**Decided:** ...
**Bugs found:** ...
**Pending:** ...
```

---

## 2026-11-22 — Agent framework + blank.pdf analysis + v0.3 planning

**Done:**
- Converted CupCake `blank.pdf` (Gemini session, 4 pages, 11/22/2026 02:59) to `blank_full.txt`.
- Read full conversation: covers GitHub bulk-add CLI, liltii-v0.2 benchmark results, multimode v0.3 planning, Unsloth training script, Qwen3.5-0.8B upgrade path, pxpipe evaluation, real-chat training data guidance.
- Built complete agent framework: AGENTS.md, PLAN.md, BACKLOG.md, SESSIONS.md, DESIGN.md, SCHEMA.md, SKILL.md.
- Ingested and sanitized 8 real WhatsApp group chat archives from Downloads (`Sylhet tour`, `Tour de Bangladesh`, `Sundarban`, `Only Discussion`, `Medical vs Engineering`, `CASE Study`, `Zia Hall RUET`, `Chudling Pong`) into `training/raw_chats/`.
- Downloaded and staged `ALERT.xlsx` and `dataset_cypher.csv` for negative filtering.
- Generated `training/dataset/liltii_v03_blended_60_40_2500.jsonl` — **2,500 total rows** blended strictly at **60.0% Bangla/Banglish (1,500 rows) : 40.0% English (1,000 rows)** with real banter, poetic quotes, gaming commentary, and technical anchors.
- Updated `training/train_unsloth_v03.py` and `training/kaggle/liltii_v03_kaggle_notebook.ipynb` to train on the new blended dataset.

**Decided:**
- **liltii v0.3 = multimode: `sarcastic, moody, flirty, cute`** — single GGUF with `[mode: X]` system tag. No separate repos.
- **Training: full 16-bit LoRA** (not QLoRA) on 0.5B — model fits in free Colab/Kaggle T4 at 16-bit without 4-bit noise degradation.
- **Hyperparameters:** r=32, lora_alpha=32, lr=2e-4 (fresh) or 1e-4 (from v0.2), max_seq_length=512, batch=4, grad_accum=4, epochs=3. Stop at 2 epochs if loss < 0.4.
- **Dataset: 1,000 rows** — 400 game events, 250 app/phone events, 350 companion chat. 90% under 15 words per response.
- **Key rule:** 30% of events must appear across all 4 modes (contrastive pairs) to prevent personality bleed.
- **Filler word ban:** No `umm, uh oh, fr, tbh, lol` stacking. Mature = economical sentences.
- **IFEval fix:** Current 24.32% score is because personality/style lives in runtime system prompts. v0.3 must bake it into training data. Shorter prompts at inference.
- **Screen reading:** ML Kit OCR on cropped HUD zones first (free, offline). Qwen3.5-0.8B + mmproj as future upgrade to remove OCR layer entirely.
- **Qwen3.5-0.8B advantages:** IFEval 52.1% (vs v0.2's 24.3%), OCRBench 79.1, ScreenSpot Pro 46.5, 201 languages, ~505 MB Q4_K_M GGUF + projector, ~45 t/s on ARM.
- **pxpipe verdict:** NOT useful for game assets — it's a text-wall compressor for LLM APIs, not a vision accelerator. Direct `MediaProjection → mmproj` is faster and cleaner.
- **Training on real chats:** YES, clean and filter first. Remove PII (names, numbers, addresses). Keep natural banter. Format into ChatML with `[mode: X]` tags. Mix: 40% chat, 35% game/app, 25% QA anchor.
- **Sampling fix for v0.3:** Use Q4_K_M (not Q4_0), `temperature=0.65, min_p=0.08, repeat_penalty=1.08` to kill gibberish and broken subwords like "l3se".

**Bugs found (from blank.pdf chat log analysis):**
- v0.2 chat log: "bhai am so sleepy thakbo fr so good nope lol tbh" and "l3se train apart" — classic slang-stuffing + context collapse (IFEval 24.3% = fine-tune overwrote base conversational logic).
- "i'm just a helpful dog" then next turn "oh hello! there's a dog!" — multi-turn context collapse. Root cause: too much casual slang in training data boosting filler-token probabilities.
- Q4_0 + loose sampling amplifies noise on tiny weights. Fix: Q4_K_M + tighter sampler.

**Pending:**
- Build liltii-v0.3 dataset (MODEL-01, MODEL-02, MODEL-03 in BACKLOG).
- Implement ActivityMonitorService for game/app detection (ACTIVITY-01, ACTIVITY-02).

---

## 2026-11-21 — Benchmarks + GitHub setup

**Done:**
- Ran liltii-v0.2-v3-q4_0.gguf on `hellaswag, arc_challenge, ifeval` via TPN benchmark service.
- Results: HellaSwag 47.58%, ARC-Challenge 31.40%, IFEval 24.32% (strict mean).
- Run cost: $6.53 (~30 min, 2 parallel lanes).
- Model at 928+ downloads on Hugging Face Bengali trending; indexed on Featherless.ai.
- bangla-smollm-135m-cupcake at 1.03k downloads.
- Investigated GitHub bulk-add collaborator via `gh` CLI loop.
- CupCake repo cleaned: removed non-essential files; kept Android app, model training, VM code.

**Decided:**
- Use `gh api --method PUT /repos/$repo/collaborators/$COLLAB` for bulk invite.
- Save TPN credits for Validate tab (compare Q4_0 vs F16 safetensors for perplexity/KL) — not for slow HellaSwag runs.
- Next model iteration: v0.3 multimode, then evaluate Qwen3.5-0.8B upgrade.

**Pending:** v0.3 training dataset construction.
## 2026-11-22 04:25 - LilTii v0.3 Training Dataset & Kaggle Setup
- Completed 60:40 blended dataset of 2,500 samples (1,500 Banglish/Bangla + 1,000 English) with 4-mode contrastive pairs, PUBG gaming triggers, YouTube/Instagram app contexts, sanitized WhatsApp tour chats, and romantic poetry quotes.
- Built standalone self-contained notebook: training/kaggle/liltii_v03_standalone_kaggle.ipynb with base64 embedded dataset and Unsloth 16-bit LoRA + GGUF export.
## 2026-11-22 05:36 - LilTii v0.3 Training Completed on Kaggle
- Successfully trained LilTii v0.3 using Qwen3.5-0.8B base with Unsloth 16-bit LoRA on Kaggle T4 GPU.
- Downloaded and verified outputs: app/src/main/assets/models/liltii-v0.3-q4_k_m.gguf (522 MB) and liltii-v0.3-mmproj.gguf (196 MB).
## 2026-11-24 01:40 - Hugging Face Model Release: Lilti_kiraa v0.3
- Successfully uploaded all GGUFs and mmproj projector to: https://huggingface.co/bayazidhs04/Lilti_kiraa-v0.3-Qwen3.5-0.8B
- Published comprehensive Model Card with real test benchmarks across all 4 personality modes.

---

## 2026-11-24 — In-App HP Pixel Reader, APK Build & Device Testing Success
**Done:**
- Added [HpBarReader.kt](file:///home/bayazid/Documents/android/CupCake_VM/app/src/main/java/com/cupcake/game/HpBarReader.kt) and [HpEventGate.kt](file:///home/bayazid/Documents/android/CupCake_VM/app/src/main/java/com/cupcake/game/HpEventGate.kt) inside `com.cupcake.game`.
- Cleaned intermediate unbundled training weights from `app/src/main/assets/models/v0.3/` into `training/archive_v03_assets/`, preventing Zip32 4 GB packaging errors.
- Built debug APK `app/build/outputs/apk/debug/app-debug.apk` (1.2 GB bundled).
- Pushed, installed, and launched `com.cupcake.debug` directly on connected Android device (`151813861E001271`).
- Verified live runtime: `LlamaEngine` JNI model copied and preloaded, TextToSpeech engine bound, Ollama client initialized without errors.
- Updated Hugging Face repositories ([`bayazidhs04/Lilti_gemma4_E2B_pruned_v0.1`](https://huggingface.co/bayazidhs04/Lilti_gemma4_E2B_pruned_v0.1) and [`bayazidhs04/Lilti_kiraa-v0.3-Qwen3.5-0.8B`](https://huggingface.co/bayazidhs04/Lilti_kiraa-v0.3-Qwen3.5-0.8B)) with full multimodal tags: `audio`, `image`, `multimodal`, `vision`, `audio-text-to-text`, `image-text-to-text`, `speech`.

---

## 2026-11-28 — Kaggle "Generalist Gaming Agent" feasibility report (research only)

**Done:**
- Read Kaggle competition Overview/Data/Rules/Code tabs (GARC, started Nov 23 2026, ~3 months left, $50k prizes).
- Audited local assets against the task: 32 real-time browser games, 4 public + 28 hidden, 200 ms decision points, 11 mouse/keyboard tools, offline notebook with llama.cpp explicitly allowed.
- Wrote comprehensive report at `docs/GGA_COMPETITION_REPORT.md`: competition facts, observation/action contracts, timing, scoring, submission mechanics, asset audit, needed vs not-needed gap analysis, hybrid architecture, 6-phase work breakdown, risks, decision gate.
- Added GGA-00..GGA-06 track to `BACKLOG.md`.
- **No implementation started** — report first per user instruction.

**Decided:**
- Custom GGUFs are *allowed* (weights attachable, llama.cpp server supported, RTX Pro 6000 96 GB) but *not ready*: v0.2 is text-only, v0.3 is multimodal but trained for chat and emits the wrong output contract.
- Strategy: port the `PUBG_Ally` hybrid — deterministic reflex policy owns the 200 ms loop; multimodal v0.3 + mmproj is a slow planner emitting `sequence` programs; `skip` yields while it thinks.
- Replace `EmotionGrammar.TAG_ACTION` with a tool-call GBNF/JSON-schema grammar. Only the 4 sample games are legal training data.
- Do notebook skeleton + reflex baseline (GGA-00..02) before any fine-tuning; benchmark the decision-model starter too.
- Deterministic sampling/seeds for all measurements (run-to-run drift 0.001–0.01 otherwise); note the ~6 h leaderboard feedback loop.

**Bugs found:** None (no code changed). Doc drift noted: `AGENTS.md` calls v0.3 "next" and Qwen3.5-0.8B "future" although `SESSIONS.md`/HF confirm v0.3 is already Qwen3.5-0.8B + mmproj.

**Pending:** GGA-00 (join/accept rules, attach weights, verify local headless run) when the user gives the go-ahead.

---

## 2026-11-28 (2) — Gemma4-E2B-pruned v0.1 checked against GGA competition

**Done:**
- Audited HF `bayazidhs04/Lilti_gemma4_E2B_pruned_v0.1` (card + HF API + `benchmark_results.json` + local `training/gemma4_pruning/prune_gemma4_e2b.py`) against the Kaggle competition.
- Appended Section 10 to `docs/GGA_COMPETITION_REPORT.md`: model spec, benchmark discrepancy, competition-fit matrix, head-to-head vs Liltii v0.3, verdict.
- Confirmed Kaggle dataset limit is 200 GB/dataset → ~3.5 GB of GGUF weights is not a blocker.

**Decided:**
- **Allowed but not ready** — same output-contract mismatch as v0.3, plus ~4.7× size, ~2× slower decode, and a non-OSI `gemma` license that needs documented exemption in the submission.
- **v0.3 remains primary slow brain**; Gemma4-pruned is an A/B challenger only after GGA-02, mainly because its Gemma 4 chat template has native `<|tool_call>` tool calling.
- Measure three things before fine-tuning anything: valid-action rate, image-encode + decode latency, groundedness on real sample-game frames.
- **Benchmark discrepancy found:** model card claims 94.2% visual grounding / 97.8% hallucination-free, but its own `benchmark_results.json` says **50.0%** (2/4 synthetic HUD tests). Treat the card figure as unreliable; fix the card later (not a competition task).
- No new GGA backlog item for this model; documented as an alternative only.

**Bugs found:** Model-card/JSON metric conflict (94.2% vs 50.0%); one failed case flagged `no_hallucination: true` while `visually_grounded: false` — inconsistent self-evaluation.

**Pending:** GGA-00 when user gives go-ahead; the A/B challenger test after GGA-02; HF card metric correction.

---

## 2026-11-28 (3) — Safe cleanup + competition mission workspace

**Done:**
- Confirmed scope with user first: safe cleanup only, competition work in a new folder in this repo, chat data preserved.
- Deleted only untracked/ignored generated junk: `blank.pdf`, `blank_full.txt`, three root `liltii-banglish-emotion-llm*.log` files, and five `__pycache__` directories (root, streamer_scraping, gemma4_pruning, PUBG_Ally, live_commentator).
- **Kept intact:** all app code, training pipeline/datasets/outputs, models, `PUBG_Ally/chat_history.json`, `training/raw_chats/`, archived logs, submodule files. Modified tracked files (`gradle.properties`, `training/kaggle/kernel-metadata.json`) untouched.
- Created `competition/gga/`: `README.md` (mission charter + rules of engagement + phase checklist), `PROTOCOL_NOTES.md` (observation/action/timing/scoring/submission facts), `agent.py` (safe `skip`-only scaffold for GGA-01, TODOs for GGA-02..05), `submission_template.ipynb` (attach inputs → start llama-server → write agent.py → start GGAInferenceServer), `.gitignore`, `runs/` via ignore rule.
- Root `.gitignore` now ignores `__pycache__/`, `*.pyc`, `competition/gga/runs/`.
- `BACKLOG.md` GGA section renamed to **ACTIVE MISSION** with workspace pointer.

**Decided:**
- Competition mission lives in `competition/gga/`; no changes to Android/ESP32/submodule for this mission.
- All competition commits use a `gga:` prefix and are pushed to `origin/main` every session.
- No model weights in git — attach to Kaggle. No fine-tuning before GGA-02 baseline.
- The scaffold is a no-op on purpose: it validates submission mechanics, not score.

**Bugs found:** None (no executed model code yet). Note: `agent.py` uses `remaining_s` as a placeholder game-boundary signal until `obs.elapsed_s` is confirmed in the real `gga.protocol.py`.

**Pending:** GGA-00 (join/accept rules, attach dataset + v0.3 GGUFs, 1-min headless smoke test) when user gives go-ahead.

---

## 2026-11-28 (4) — GGA-00 completed: account entered, dataset attached locally, smoke test passed

**Done:**
- Checked Kaggle account state via CLI: `userHasEntered: True`, 0 submissions, 5 remaining today → **already joined**; CLI has no `join` command and rule acceptance must happen in the browser anyway.
- Downloaded competition dataset (354 MB) to `competition/gga/data/` (gitignored).
- Read the real `gga/protocol.py` (API_VERSION 1.3) and corrected the scaffold: `obs.info` is a **dict** (not an object), game boundary is `obs.elapsed_s` (plus `last_action == {}` edge case), `ToolSpec` uses `.name`, `Action` has `.meta`, `validate()`/`check_action()` available.
- Rewrote `competition/gga/agent.py` accordingly; expanded `PROTOCOL_NOTES.md` with verified harness facts.
- Set up local test env: `competition/gga/.venv` (system Python externally managed), installed playwright 1.60.0; bundled browser binaries needed `chmod +x` after unzip; `PLAYWRIGHT_BROWSERS_PATH=.../kit/browsers`.
- **1-minute headless smoke test passed:** `{"game":"off_line","steps":299,"status":"ok","action_errors":[],"frames_seen":1196,"score":null}`.
- Updated README (verified setup section + status), BACKLOG (GGA-00 done), workspace `.gitignore` (`.venv/`).

**Decided:**
- Scaffold stays a safe no-op; it validates submission mechanics only. No model server yet — that is GGA-01/03.
- Models can be swapped between submissions: attach different GGUFs to a new notebook version, resubmit; only the two selected final submissions matter. Must remain entered before Feb 22 2027.
- Local runs report `score: null`; all scoring comes from Kaggle reruns (~6 h).

**Bugs found:** Bundled Chromium/`chrome-headless-shell` lose executable bit on unzip → `EACCES` until `chmod +x` (documented in README). System pip blocked by PEP 668 → use the project venv.

**Pending:** GGA-01 (notebook: attach v0.3 GGUFs, start llama-server, write agent.py, run GGAInferenceServer), then GGA-02 reflex baseline.

---

## 2026-11-28 (5) — Model-size limits + full rules compiled (no implementation)

**Done:**
- Answered the user's two questions by research only: maximum model size and all rules/regulations.
- Added `competition/gga/RULES_AND_LIMITS.md`: platform ceilings (200 GB/dataset, 20 GB output, 30 GB CPU RAM, RTX Pro 6000 96 GB, 15-min startup, 9-h runtime, 90 s/decision, 5 submissions/day), practical size guidance (0.5–3B Q4 recommended; ≤10 GB attached total), and all competition rules — task/submission, scoring, timeline/prizes, and all 18 legal sections (C.1–C.18) — plus red lines and open items.
- Added a pointer to it in `competition/gga/README.md`.

**Decided:**
- No competition-specific numeric model cap exists; latency (200 ms grid, 90 s deadline) is the binding constraint, not storage.
- Keep v0.3 (~718 MB) as default; Gemma4-pruned (~3.5 GB) is an attach-safe challenger; 13B+ is not worth it for real-time control.
- No competition-specific legal sections A/B were visible on the Rules tab; exact OSI license and max team size are not stated on the pages checked — recheck before final submission.

**Bugs found:** None (documentation only).

**Pending:** GGA-01 and GGA-02 unchanged; user asked not to jump ahead.




