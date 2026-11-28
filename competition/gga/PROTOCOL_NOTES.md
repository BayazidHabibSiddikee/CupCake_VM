# GGA Protocol Notes

Transcribed from the Kaggle competition **Data** tab on 2026-11-28. Verify every field against `gga/protocol.py` once the competition dataset is attached — that file is authoritative.

## Observation

| Field | Meaning |
| --- | --- |
| `obs.image` | JPEG of the current frame at viewport size; **pixel coordinates are the action coordinates** |
| `obs.frames` | Frames since the previous decision point |
| `obs.history` | Up to 8 full-size earlier frames since the previous observation (evenly spread when more) |
| `obs.info` | `description`, `controls`, `remaining_s`, `width`, `height` |
| `obs.last_action` | How the previous reply went, including why it was refused |
| `obs.elapsed_s` | Drops back near 0 when a new game starts → reset per-game state |

## Actions — 11 tools

`click`, `move`, `drag`, `scroll` (mouse at `x`,`y`); `press_key`, `hold_keys`, `key_down`, `key_up` (keyboard; printable chars or names like `ArrowLeft`, `Space`, `Enter` — see `gga.protocol.NAMED_KEYS`); `wait` (replace running inputs, idle `duration_ms`); `sequence` (timed program of up to **200 steps that runs while the model thinks**); `skip` (change nothing — lets running inputs play on).

- Tool JSON schemas are bounded to the viewport and passed in `tools`.
- A refused action changes nothing; the reason arrives in the next `obs.last_action`.
- Every reply except `skip` replaces leftover running inputs (a cut-short `press_key` hold is released).

## Timing

- 20 fps; decision point every 4 frames = **200 ms**.
- Reply takes effect at the first decision point after arrival; slow replies land later but are **never dropped**.
- **90 s** per decision limit, else the game ends with its best score so far.
- Exception or unusable reply → `skip`.

## Scoring

Per game: `min(1, max(0, (value - floor) / (human - floor)))`. Public LB = mean of 16 games (including the 4 samples); private LB = mean of the other 16 and decides ranking. Up to two final submissions; better private score wins.

Games are deterministic; variation comes from the agent. Sampling or variable reply timing moves repeat submissions by ~0.001–0.01.

## Submission contract

```python
from gga.protocol import Action, Observation, ToolSpec

class Agent:
    def __init__(self):
        ...  # load model once, before game 1

    def step(self, obs: Observation, tools: list[ToolSpec]) -> Action:
        return Action(tool="click", params={"x": 320, "y": 240})
```

- **One instance plays all 32 games back to back** — reset per-game state when `obs.elapsed_s` drops near 0.
- Startup budget (installs, model server, `__init__`): **15 minutes**. Notebook runtime: **9 hours**. **No internet.**
- Attach the competition dataset plus model weights/wheels; start a localhost model server in the background (llama.cpp is explicitly supported).
- Final cell must run unconditionally:
  ```python
  from kaggle_evaluation.gga.gga_inference_server import GGAInferenceServer
  GGAInferenceServer().run()
  ```
  If guarded by `KAGGLE_IS_COMPETITION_RERUN`, call `server.run_local_gateway()` in the other branch.
- Scoring after submit takes ~6 hours (Kaggle reruns all 32 games × 10 min).

## Local test (no score)

```bash
pip install playwright==1.60.0 pillow
playwright install chromium
GGA_HEADLESS=1 python -m gga.game --game off_line --agent path/to/agent.py --minutes 1
```

## Dataset files

| Path | Contents |
| --- | --- |
| `gga/` | Harness: `gga.protocol` (interface), `gga.game` (local play) |
| `kaggle_evaluation/` | `GGAInferenceServer` |
| `assets/` | Four sample games |
| `kit/` | Offline Playwright/Chromium installs + compressed-tensors |
