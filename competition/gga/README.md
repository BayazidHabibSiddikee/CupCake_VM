# GGA Mission Workspace

**Mission:** build the offline agent for Kaggle's [Generalist Gaming Agent](https://www.kaggle.com/competitions/generalist-gaming-agent) competition and submit it before **Mar 1, 2027** (entry/rules deadline **Feb 22, 2027**).

**Status (2026-11-28):** GGA-00 ✅ — account already entered, dataset downloaded (354 MB) into `data/`, and the 1-minute headless smoke test passed (299 steps, 0 action errors). GGA-01 onward not started.
**Full analysis:** [`../../docs/GGA_COMPETITION_REPORT.md`](../../docs/GGA_COMPETITION_REPORT.md) (facts, asset audit, gaps, architecture, risks, Gemma4 comparison).
**Backlog:** [`../../BACKLOG.md`](../../BACKLOG.md) → section **GGA COMPETITION** (GGA-00 … GGA-06).

---

## Mental model — what we are actually building

An **external bot/agent**, not a game mod. It runs outside the game in its own container, sees only screenshots + a short text brief, and sends mouse/keyboard events through the harness (Playwright) at the browser-input layer — exactly like a human playing. It has **no access to game code, memory, internal state, DOM state or APIs**, and cannot modify the game. In-game outcomes ("kills", points, levels) come only from those input events. The game keeps running at 20 fps while the agent decides, and one agent must handle all 32 games, including 28 it has never seen. This is an offline benchmark in sandboxed Chromium — not an online cheat tool.

## Rules of engagement

1. **All competition code lives here** (`competition/gga/`). Do not edit the Android app, ESP32 firmware, or `app/src/main/cpp/third_party/llama.cpp/` for this mission.
2. **Chat data is off-limits:** `PUBG_Ally/chat_history.json` and `training/raw_chats/` are preserved, untouched.
3. **Models are not committed to git.** Attach GGUFs to the Kaggle notebook/dataset instead. Keep local paths in config, never hardcode secrets.
4. **Commit and push every session** to `origin/main` with a short `gga:` prefixed message.
5. **Measure before tuning.** No fine-tuning until the reflex baseline (GGA-02) produces a nonzero score on all four sample games.
6. **Determinism:** temperature 0 / fixed seeds for scored comparisons; the leaderboard has ~6 h feedback, so local `gga.game` runs are the primary loop.

## Files in this workspace

| File | Purpose |
| --- | --- |
| `README.md` | This charter and phase checklist |
| `PROTOCOL_NOTES.md` | Observation/action/timing/scoring facts transcribed from the Kaggle Data tab |
| `RULES_AND_LIMITS.md` | Model-size ceilings, platform limits, and the full competition rules (technical + legal) |
| `agent.py` | `Agent` scaffold — TODOs marked; not runnable until the dataset is attached |
| `submission_template.ipynb` | Kaggle notebook skeleton: attach weights → start llama-server → write agent.py → start server |
| `runs/` | Local test logs/outputs (gitignored) |

## Phase checklist

- [x] **GGA-00** Account already entered (`userHasEntered: True`), dataset downloaded, 1-min headless smoke test passed with the `skip` scaffold. Weights still need attaching to the Kaggle notebook.
- [ ] **GGA-01** Notebook skeleton boots `llama-server` (mmproj), writes `agent.py`, ends with `GGAInferenceServer().run()`; submission accepted.
- [ ] **GGA-02** Reflex baseline: brief parser + deterministic heuristics over the 11 tools; `sequence`/`skip` orchestration; game reset on `elapsed_s ≈ 0`.
- [ ] **GGA-03** Vision: downscale `obs.image` → mmproj, tool-call grammar, latency budget; SLM emits cached action programs.
- [ ] **GGA-04** Trajectory fine-tune from the 4 sample games, LoRA on Qwen3.5-0.8B, GGUF export, A/B vs baseline and the decision-model starter.
- [ ] **GGA-05** Generalization hardening: hidden-genre robustness, refusal recovery, stable seeds, full 32-game run.
- [ ] **GGA-06** Select two final submissions before Mar 1 2027.

## Verified local setup (GGA-00)

From the repo root:

```bash
# Dataset (354 MB) — already done once; skip if data/ exists
kaggle competitions download -c generalist-gaming-agent -p competition/gga/data --unzip

# Isolated env (system Python is externally managed)
python3 -m venv --system-site-packages competition/gga/.venv
competition/gga/.venv/bin/pip install playwright==1.60.0

# Unzip drops the executable bit on the bundled browsers — restore it
find competition/gga/data/kit/browsers -type f \
  \( -name 'chrome' -o -name 'chrome-headless-shell' -o -name 'ffmpeg-linux' \) \
  -exec chmod +x {} +
```

Then, from `competition/gga/data`:

```bash
PLAYWRIGHT_BROWSERS_PATH=$PWD/kit/browsers GGA_HEADLESS=1 \
  ../.venv/bin/python -m gga.game --game off_line --agent ../agent.py --minutes 1
```

Result on 2026-11-28: `{"status": "ok", "steps": 299, "frames_seen": 1196, "action_error_count": 0, "score": null}` — local runs never report a score.

**Model choice:** `liltii-v0.3-q4_k_m.gguf` + `liltii-v0.3-mmproj.gguf` is the primary slow brain (~718 MB, ~48 tok/s reported). `Lilti_gemma4_E2B_pruned_v0.1` (~3.5 GB, ~21.8 tok/s, native `<|tool_call>` template, non-OSI license) is a documented A/B challenger, not the default — see report §10.
