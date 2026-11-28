"""GGA agent SCAFFOLD — submission-mechanics baseline only (GGA-01).

Verified against the downloaded competition harness: API_VERSION 1.3,
`gga/protocol.py`. This agent returns `skip` every step. It intentionally scores
~0: its job is to prove the notebook, local server and submission path work.

Do NOT treat this as the competition agent. See README.md / BACKLOG.md for
GGA-02 (reflex policy), GGA-03 (vision + tool grammar), GGA-04 (fine-tune).

Local smoke test (from competition/gga/data, Python 3.11+):
  GGA_HEADLESS=1 python -m gga.game --game off_line \
      --agent ../agent.py --minutes 1
"""

from __future__ import annotations

from typing import Any

try:
    from gga.protocol import Action, Observation, ToolSpec, validate
except ImportError as exc:  # pragma: no cover - dataset not attached yet
    raise SystemExit(
        "gga.protocol not found. Attach the competition dataset and run from "
        "competition/gga/data (see competition/gga/README.md)."
    ) from exc


VALID_TOOLS = frozenset(
    {
        "click", "move", "drag", "scroll",
        "press_key", "hold_keys", "key_down", "key_up",
        "wait", "sequence", "skip",
    }
)


class Agent:
    """One instance plays all 32 games; reset per-game state at each boundary."""

    def __init__(self) -> None:
        # TODO GGA-01: connect to the localhost llama-server (v0.3 + mmproj).
        # TODO GGA-03: load the tool-call grammar / constrained decoder.
        self._last_elapsed_s = 0.0
        self._steps_in_game = 0
        self._brief: dict[str, Any] = {}

    def _reset_game_if_needed(self, obs: Observation) -> None:
        """Protocol: a new game starts when elapsed_s restarts near 0, or when
        the same elapsed_s arrives with last_action {} (game ended at its first
        observation)."""
        elapsed = float(obs.elapsed_s)
        new_game = (
            self._steps_in_game >= 1
            and (
                elapsed < self._last_elapsed_s - 0.25
                or elapsed <= 0.25
                or obs.last_action == {}
            )
        )
        if new_game:
            self._brief = {}
            self._steps_in_game = 0
        self._last_elapsed_s = elapsed
        self._steps_in_game += 1

    def _parse_brief(self, obs: Observation) -> dict[str, Any]:
        """TODO GGA-02: turn obs.info['description'] / ['controls'] into an
        action vocabulary. This is the main generalisation lever for the 28
        hidden games. obs.info is a plain dict, not an object."""
        info: dict[str, Any] = obs.info or {}
        return {
            "description": info.get("description", ""),
            "controls": info.get("controls", ""),
            "width": info.get("width"),
            "height": info.get("height"),
            "game_id": info.get("game_id"),
            "title": info.get("title"),
            "genre": info.get("genre"),
        }

    def step(self, obs: Observation, tools: list[ToolSpec]) -> Action:
        """Return exactly one valid tool call. Always safe: fallback is `skip`."""
        self._reset_game_if_needed(obs)
        self._brief = self._parse_brief(obs)

        # ToolSpec has .name / .description / .parameters (JSON schema).
        offered = {tool.name for tool in tools} & VALID_TOOLS
        if not offered:
            return Action("skip", {})

        # TODO GGA-02: deterministic reflex policy (heuristics / behavior tree).
        # TODO GGA-03: publish cached plans via `sequence`, yield with `skip`
        #              while the multimodal model thinks.
        # TODO GGA-05: handle obs.last_action refusals/dropped programs; enforce
        #              a hard per-decision latency budget (< 90 s, aim < 1 s).
        if "skip" in offered:
            return Action("skip", {})

        # `skip` should always be offered; `wait` is the safest remaining no-op.
        tool = "wait" if "wait" in offered else next(iter(offered))
        params: dict[str, Any] = {"duration_ms": 200} if tool == "wait" else {}
        try:
            width = int(self._brief["width"] or 0)
            height = int(self._brief["height"] or 0)
            params = validate(tool, params, width, height)
        except Exception:
            return Action("skip", {})
        return Action(tool, params)
