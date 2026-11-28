# GGA Mission Workspace

**Mission:** build the offline agent for Kaggle's [Generalist Gaming Agent](https://www.kaggle.com/competitions/generalist-gaming-agent) competition and submit it before **Mar 1, 2027** (entry/rules deadline **Feb 22, 2027**).

**Status (2026-11-28):** Phase 0 — workspace ready, competition dataset **not yet attached**, no agent run yet.
**Full analysis:** [`../../docs/GGA_COMPETITION_REPORT.md`](../../docs/GGA_COMPETITION_REPORT.md) (facts, asset audit, gaps, architecture, risks, Gemma4 comparison).
**Backlog:** [`../../BACKLOG.md`](../../BACKLOG.md) → section **GGA COMPETITION** (GGA-00 … GGA-06).

---

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
| `agent.py` | `Agent` scaffold — TODOs marked; not runnable until the dataset is attached |
| `submission_template.ipynb` | Kaggle notebook skeleton: attach weights → start llama-server → write agent.py → start server |
| `runs/` | Local test logs/outputs (gitignored) |

## Phase checklist

- [ ] **GGA-00** Join + accept rules, attach competition dataset and weights, run `gga.game` headless for 1 min with the stub agent.
- [ ] **GGA-01** Notebook skeleton boots `llama-server` (mmproj), writes `agent.py`, ends with `GGAInferenceServer().run()`; submission accepted.
- [ ] **GGA-02** Reflex baseline: brief parser + deterministic heuristics over the 11 tools; `sequence`/`skip` orchestration; game reset on `elapsed_s ≈ 0`.
- [ ] **GGA-03** Vision: downscale `obs.image` → mmproj, tool-call grammar, latency budget; SLM emits cached action programs.
- [ ] **GGA-04** Trajectory fine-tune from the 4 sample games, LoRA on Qwen3.5-0.8B, GGUF export, A/B vs baseline and the decision-model starter.
- [ ] **GGA-05** Generalization hardening: hidden-genre robustness, refusal recovery, stable seeds, full 32-game run.
- [ ] **GGA-06** Select two final submissions before Mar 1 2027.

## First commands (once the dataset is attached)

```bash
# From the competition dataset root (Python 3.11+)
pip install playwright==1.60.0 pillow
playwright install chromium

# Fast smoke test — no score reported locally
GGA_HEADLESS=1 python -m gga.game --game off_line \
  --agent /path/to/CupCake_VM/competition/gga/agent.py --minutes 1
```

**Model choice:** `liltii-v0.3-q4_k_m.gguf` + `liltii-v0.3-mmproj.gguf` is the primary slow brain (~718 MB, ~48 tok/s reported). `Lilti_gemma4_E2B_pruned_v0.1` (~3.5 GB, ~21.8 tok/s, native `<|tool_call>` template, non-OSI license) is a documented A/B challenger, not the default — see report §10.
