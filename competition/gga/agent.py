"""GGA agent SCAFFOLD — submission-mechanics baseline only.

Status: GGA-01. This agent returns `skip` every step. It is intentionally a no-op:
its job is to prove the notebook, the local server and the submission path work,
not to score points. Expected score ≈ 0.

Do NOT treat this as the competition agent. See README.md / BACKLOG.md phases
GGA-02..GGA-05 for the reflex policy, vision path and fine-tune.

`gga.protocol` only exists after the competition dataset is attached. Local
smoke test: GGA_HEADLESS=1 python -m gga.game --game off_line --agent <this file> --minutes 1
"""

from __future__ import annotations

from typing import Any

try:
    from gga.protocol import Action, Observation, ToolSpec
except ImportError as exc:  # pragma: no cover - dataset not attached yet
    raise SystemExit(
        "gga.protocol not found. Attach the competition dataset first "
        "(see competition/gga/README.md)."
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
        self._game_key: Any = None
        self._brief: dict[str, Any] = {}
        self._steps_in_game = 0

    def _reset_game_if_needed(self, obs: Observation) -> None:
        """Detect a new game: elapsed_s drops back near 0."""
        remaining = getattr(getattr(obs, "info", None), "remaining_s", None)
        key = round(float(remaining or 0.0), 0)
        if key != self._game_key:
            self._game_key = key
            self._brief = {}
            self._steps_in_game = 0
        # NOTE: replace with obs.elapsed_s once the real field is confirmed in
        # gga.protocol.py. remaining_s is a placeholder for the same boundary.

    def _parse_brief(self, obs: Observation) -> dict[str, Any]:
        """TODO GGA-02: turn obs.info.description/controls into an action vocabulary.

        This is the main generalisation lever for the 28 hidden games.
        """
        info = getattr(obs, "info", None)
        if info is None:
            return {}
        return {
            "description": getattr(info, "description", ""),
            "controls": getattr(info, "controls", ""),
            "width": getattr(info, "width", None),
            "height": getattr(info, "height", None),
        }

    def step(self, obs: Observation, tools: list[ToolSpec]) -> Action:
        """Return exactly one valid tool call. Always safe: fallback is `skip`."""
        self._reset_game_if_needed(obs)
        self._brief = self._parse_brief(obs)
        self._steps_in_game += 1

        # Validate against the tools actually offered by the harness.
        offered = {
            getattr(tool, "tool", None) or getattr(tool, "name", None)
            for tool in tools
        } - {None}
        allowed = offered & VALID_TOOLS or VALID_TOOLS

        # TODO GGA-02: deterministic reflex policy (heuristics / behavior tree).
        # TODO GGA-03: when the SLM is ready, publish cached plans via `sequence`
        #              and yield with `skip` while it thinks.
        # TODO GGA-05: handle obs.last_action refusals; enforce a hard latency budget.
        if "skip" in allowed:
            return Action(tool="skip", params={})

        # `skip` should always be available; if not, `wait` is the safest no-op.
        fallback = "wait" if "wait" in allowed else next(iter(allowed))
        params = {"duration_ms": 200} if fallback == "wait" else {}
        return Action(tool=fallback, params=params)
