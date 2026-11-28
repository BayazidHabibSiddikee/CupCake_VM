# BACKLOG.md — CupCake Task Board

> Ordered by priority within each section. AI agents: pick from **Now** first.
> When done: move item to **Done**, add entry to `SESSIONS.md`.

---

## 🔴 NOW (Active Sprint)

- [x] **[MODEL-01]** Generate liltii-v0.3 training dataset — Ingested real WhatsApp group chats (RUET, tour groups, hall groups) + poetic quotes + gaming/app events into a **60:40 (Bangla/Banglish : English) blended 2,500-row dataset** (`training/dataset/liltii_v03_blended_60_40_2500.jsonl`).
- [x] **[MODEL-02-PREP]** Build Unsloth training script and Kaggle/Colab notebook (`training/train_unsloth_v03.py`, `training/kaggle/liltii_v03_kaggle_notebook.ipynb`) with full 16-bit LoRA, target module config, `train_on_responses_only`, and Q4_K_M GGUF export.
- [ ] **[MODEL-02-RUN]** Execute training on Kaggle / Colab GPU (T4), verify sanity check output for unmasked tokens, and export `liltii-v0.3-q4_k_m.gguf`.
- [ ] **[ACTIVITY-01]** Implement `ActivityMonitorService` — detect foreground app package name via `ActivityManager.getRunningAppProcesses()` or `AccessibilityService`. Classify into: gaming, youtube, social, browsing, chat, productivity, idle.
- [ ] **[ACTIVITY-02]** Pass detected activity context to `LlamaEngine` as metadata prefix: `[ctx: game] [app: PUBG] [event: ...]`.

---

## 🟡 NEXT (Queued)

- [ ] **[SCREEN-01]** Implement screen capture pipeline — `MediaProjection` API in foreground service (declare `foregroundServiceType="mediaProjection"` in manifest). Capture 1 frame every 2–3s.
- [ ] **[SCREEN-02]** Pixel-diff gate — shrink each captured frame to 32×32 grayscale, compare to last frame. Only trigger OCR/LLM when significant change detected.
- [ ] **[SCREEN-03]** ML Kit OCR on cropped HUD zones — crop kill feed (top-right), HP bar (bottom-left), center banner ("Eliminated", "Victory"). Parse key game events.
- [ ] **[COMMENT-01]** Game event → commentary prompt pipeline. Format: `[mode: X] [ctx: game] [app: PUBG] [event: Y] [detail: Z]`. Cap n_ctx=512, max_tokens=35, n_threads=2–4.
- [ ] **[COMMENT-02]** Commentary cooldown — enforce 8–15s between unsolicited comments. Tap on floating bubble overrides cooldown.
- [ ] **[MODE-01]** Multimode system prompt switching — `LlamaEngine` accepts `CompanionMode` enum (`CUTE, SARCASTIC, MOODY, FLIRTY`). System prompt uses `[mode: X]` tag. User can set preferred mode in Settings.
- [ ] **[BLE-01]** Implement `BleGattClient.kt` with `BluetoothGatt` + `BluetoothGattCallback` — scan, connect, discover NUS services, MTU negotiation (517 bytes), notify subscription.
- [ ] **[BLE-02]** `SensorReading` Room entity + DAO + migration v1→v2. Fields: `id, deviceId, timestamp, accelX, accelY, accelZ, gyroX, gyroY, gyroZ, battery`.
- [ ] **[BLE-03]** `SensorRepository` exposing `Flow<SensorReading>`. Parse binary protocol via `ProtocolDecoder.kt` (Kotlin port of `protocol.cpp`).
- [ ] **[HILT-01]** Re-enable Hilt KAPT in `app/build.gradle.kts` (lines 255, 259). Fix any annotation processor conflicts. Run `./gradlew assembleDebug` to confirm clean build.
- [ ] **[OLLAMA-01]** Convert `OllamaEngine` callback → `Flow<String>` with typed error hierarchy (`NetworkError`, `ModelNotFoundError`, `TokenLimitError`).
- [ ] **[OLLAMA-02]** Model selection bottom sheet in ChatScreen — fetch available models, let user pick per-conversation.

---

## 🟢 GGA COMPETITION — ACTIVE MISSION (Kaggle)

> **Workspace:** `competition/gga/` (charter, protocol notes, agent scaffold, submission notebook).
> Full analysis in `docs/GGA_COMPETITION_REPORT.md`. Do phases in order; measure the reflex baseline before spending GPU time on a fine-tune.

- [x] **[GGA-00]** Account already entered (`userHasEntered: True`); dataset downloaded to `competition/gga/data/`; headless 1-min `off_line` smoke test passed (299 steps, 0 action errors) with the `skip` scaffold. Still TODO: attach `liltii-v0.3-q4_k_m.gguf` + `liltii-v0.3-mmproj.gguf` to the Kaggle notebook (GGA-01).
- [ ] **[GGA-01]** Notebook skeleton: background `llama-server` on localhost, `%%writefile /kaggle/working/agent.py` with `Agent.__init__` / `step(obs, tools) -> Action`, end cell `GGAInferenceServer().run()`; confirm submission accepted.
- [ ] **[GGA-02]** Reflex baseline: parse `obs.info.description`/`controls`, deterministic heuristic policy over the 11 tools, `sequence`/`skip` orchestration, game-boundary reset via `obs.elapsed_s`; nonzero score on all 4 sample games.
- [ ] **[GGA-03]** Vision integration: downscale `obs.image` → mmproj, replace emotion grammar with a tool-call grammar, hard latency budget (<90 s, aim ~1 s), SLM emits cached action programs.
- [ ] **[GGA-04]** Trajectory fine-tune: collect `(frame + brief + history) → tool call` data from the 4 sample games, LoRA on Qwen3.5-0.8B (action tokens only), GGUF export, A/B vs baseline and vs decision-model starter.
- [ ] **[GGA-05]** Generalization hardening: prompt/action randomization, refusal recovery via `obs.last_action`, deterministic seeds, full 32-game stability run.
- [ ] **[GGA-06]** Select two final submissions before Mar 1 2027, verify both reruns complete.

---

## 🔵 LATER (Backlog)

- [ ] **[VISION-01]** Upgrade base model to Qwen3.5-0.8B + mmproj. Load via llama-mtmd path. Remove ML Kit OCR pipeline — model reads screen directly. Runtime: `--temp 0.7 --top-p 0.8 --top-k 20 --presence-penalty 1.5 --chat-template-kwargs '{"enable_thinking":false}'`.
- [ ] **[VISION-02]** Downscale MediaProjection frames to ~360px height before passing to mmproj. Crop to HUD region (not full background).
- [ ] **[PUBG-01]** PUBG_Ally standalone app — overlay-only commentator without full CupCake companion. Lighter footprint.
- [ ] **[GESTURE-01]** ESP32: Implement gesture detection (tap, shake, rotate) in `sensorTask`. Emit `MSG_TYPE_EVENT` with gesture type. Android: handle in `ProtocolDecoder`.
- [ ] **[ESP-MTU]** Add MTU negotiation to `ble.cpp` — `conn->requestMtu(517)` during connection setup.
- [ ] **[CHART-01]** Real-time sensor chart (Compose Canvas) consuming `SensorRepository`. Live accel/gyro visualization in DeviceScreen.
- [ ] **[CI-01]** GitHub Actions — `./gradlew lint test assembleDebug` on every PR.
- [ ] **[ONBOARD-01]** Onboarding flow: device pairing → Ollama setup → model download guide.
- [ ] **[EXPORT-01]** Q4_K_M export alongside Q4_0 for liltii-v0.3. Q4_K_M has sharper Banglish fluency at same RAM footprint.

---

## ✅ DONE

- [x] On-device GGUF companion (liltii-v0.2, Qwen2.5-0.5B) with GBNF grammar (Nov 2026)
- [x] 15 mini-games with ML Q-learning bots (adaptive difficulty, jealousy/anger) (Nov 2026)
- [x] Points/XP system with achievements (Nov 2026)
- [x] Character system (Marin + custom + SillyTavern card import/export) (Nov 2026)
- [x] ESP32-S3 WebSocket bridge (face/motor/audio frames) (Nov 2026)
- [x] BLE NUS server on ESP32 + BleGattClient scaffold on Android (Nov 2026)
- [x] Floating pet overlay — `ShimejiPetService` (Nov 2026)
- [x] Remote provider support (Ollama, OpenAI-compatible) (Nov 2026)
- [x] Energy system + freemium shell (Nov 2026)
- [x] BanglishTranslator + EmotionClassifier (Nov 2026)
- [x] ProactiveEngagementManager + DemandManager (Nov 2026)
- [x] liltii-v0.2 benchmark run: HellaSwag 47.58%, ARC 31.40%, IFEval 24.32% (Nov 22 2026)
- [x] Identified IFEval weakness — fix: bake personality into training data, not runtime prompts (Nov 22 2026)
- [x] Agent framework docs: AGENTS.md, PLAN.md, BACKLOG.md, SESSIONS.md, DESIGN.md, SCHEMA.md, SKILL.md (Nov 22 2026)
