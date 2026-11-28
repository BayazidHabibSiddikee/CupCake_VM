# GGA Protocol Notes (verified against downloaded harness)

Source: Kaggle Data tab + `competition/gga/data/gga/protocol.py` (**API_VERSION 1.3**), downloaded 2026-11-28. `gga/protocol.py` is authoritative; this is a quick reference.

## Observation — `Observation` dataclass

| Field | Meaning |
| --- | --- |
| `image` | JPEG of the grid-point frame at viewport size; **pixels are the action coordinates**. Drawn *before* inputs applied there. |
| `elapsed_s` | Game seconds since this episode started; **restarts near 0 for the next game**. If a game ends at its first observation, the next game can show the same `elapsed_s` with `last_action == {}` — handle both. |
| `info` | **Plain dict**: `description`, `controls`, `remaining_s`, `width`, `height`; `game_id`, `title`, `genre` for the 4 sample games only; plus `fps`, `grid_frames`, `watchdog_frames`, `max_keys`, `max_steps`. |
| `frames` | Frames since previous decision point, oldest first, as `(elapsed_s, jpeg)`; last one is `image`. |
| `held` | `{"keys": [...], "buttons": [...], "pointer": [x,y] or None}` after your reply. |
| `program_left_s`, `program` | Running program state; the last entry holds until the watchdog releases it. |
| `last_action` | `{"tool", "ok", "error", "received_frame", "run_frame", "wall_latency_s", "frame", "replaced", "dropped"}`; `notice` appears in **local runs only** (`decision_timeout`, `agent_exception`, `unusable_reply`, `agent_restarted`) — a notice means your reply was NOT played. |
| `frame` | Episode frame this observation shows. |
| `history` | Up to 8 evenly-spread earlier frames since your previous observation, same size as `image`. **Do not keep whole observations — frames are large.** |

## Input modalities — what actually reaches the agent

- **Image: yes, the primary signal.** `image`, `frames`, `history` are all JPEGs. Multiple frames can be fed to a vision encoder, but there is no video stream object — just frame lists.
- **Text: yes, but only structured text.** `info['description']`, `info['controls']`, metadata (fps/grid_frames/remaining_s/width/height), `last_action` and the 11 `ToolSpec` descriptions/schemas. There is **no dialogue or conversation** with the game.
- **Audio: NO.** There is no `audio`/sound field in `Observation`, and no audio path in `kaggle_evaluation`. Games contain `.ogg` assets and Chromium decodes audio for its own lockstep, but **none of it is given to the agent**. An audio-capable model gets zero extra signal.
- **Structured state: yes.** `held`, `program`, `program_left_s`, `frame`, `elapsed_s` are crucial for control — easy to overlook if you only feed pixels to the model.

**Implication:** a text+image model is the right shape; audio support is dead weight here. The hard part is action grounding (pixels + brief → tool call), not understanding speech.

## Action — `Action(tool, params, meta)`

`meta` is agent-only notes (logged, never sent). `params`/`meta` must be JSON values. Use `gga.protocol.validate(tool, params, width, height)` to check a reply exactly as the harness does; `check_action` checks the schema only. `valid_key()` and `normalize_key()` handle key aliases (`space`, `up`, `esc`, `KeyW`, `Digit1`, …).

## Tools — `tools(width, height) -> list[ToolSpec]`

`ToolSpec(name, description, parameters)`; `parameters` is a JSON-schema subset with bounded x/y. 11 tools:

`click`, `move`, `drag`, `scroll`, `press_key`, `hold_keys`, `key_down`, `key_up`, `wait`, `sequence`, `skip`.

- `sequence` takes 1–200 steps; each step is the **complete** set of keys/buttons to hold, optional `x`/`y` (both or neither), and exactly one of `duration_ms` (1–10000) or `duration_frames`. It runs while you think; a new reply replaces what is left.
- `skip` leaves the running program alone and has no params. A refused reply also plays `skip`.
- Max 8 keys held at once; `MAX_STEPS=200`, `MAX_HOLD_MS=10000`.
- Every reply except `skip` replaces leftover inputs. A program's last state stays held 10 s after it ends unless a reply changes it.

## Timing

- 20 fps, decision point every 4 frames = **200 ms** (`info.fps`, `info.grid_frames`).
- Reply is "received" at the frame the game had reached on arrival (or full-speed equivalent if the game renders slowly), and takes effect at the next grid point.
- **90 s** per decision in evaluation (`agent_worker.DECISION_LIMIT_S`); local runs play `skip` instead but don't end the game. Exception/unusable reply → `skip`.
- `remaining_s` is game time, not necessarily wall-clock time.

## Scoring

`min(1, max(0, (value - floor) / (human - floor)))`. Public LB = mean of 16 games (incl. 4 samples); private LB = mean of the other 16 and decides ranking. Up to two final submissions; better private score wins. Games are deterministic; agent sampling/timing causes ~0.001–0.01 drift, so use temperature 0 and fixed seeds for comparisons.

## Submission contract

```python
from gga.protocol import Action, Observation, ToolSpec

class Agent:
    def __init__(self): ...  # load model once, before game 1
    def step(self, obs: Observation, tools: list[ToolSpec]) -> Action: ...
```

- **One instance plays all 32 games** — reset per-game state at the boundaries described above.
- Startup (installs + model server + `__init__`): **15 min**. Notebook runtime: **9 h**. **No internet.**
- Attach competition dataset + weights; start a localhost model server in the background (llama.cpp explicitly supported).
- Last cell must run unconditionally:
  ```python
  from kaggle_evaluation.gga.gga_inference_server import GGAInferenceServer
  GGAInferenceServer().run()
  ```
  If guarded by `KAGGLE_IS_COMPETITION_RERUN`, call `server.run_local_gateway()` otherwise.
- Scoring after submit takes ~6 h (Kaggle reruns 32 games × 10 min).

## Local test (no score)

From `competition/gga/data` (Python 3.11+):

```bash
pip install playwright==1.60.0 pillow
playwright install chromium   # offline kit/ has browsers + wheels
GGA_HEADLESS=1 python -m gga.game --game off_line --agent ../agent.py --minutes 1
```

## Dataset layout

`gga/` (harness: `protocol.py`, `game.py`, `runner.py`, `browser.py`, …), `kaggle_evaluation/` (`GGAInferenceServer`), `assets/` (4 sample games by genre: Action, Adventure, Racing, Strategy), `kit/` (offline debs/wheels/browsers + compressed-tensors), `submission/`.
