# GGA — Model Size Limits & Rules of the Competition

Compiled 2026-11-28 from the competition Overview/Data/Rules tabs, Kaggle Datasets/Notebooks/Competitions docs, the downloaded `kaggle_evaluation` README, and the live CLI (`kaggle competitions list`, `submission-limits`).

---

## 1. Model size: what is the maximum?

**There is no competition-specific numeric model-size cap.** The ceiling comes from Kaggle platform limits and, more importantly, from the real-time loop.

### Hard platform ceilings

| Constraint | Value | Source |
| --- | --- | --- |
| Attached input data per dataset | **200 GB** (200 GB max private datasets total) | Kaggle Datasets → Limitations |
| Saved notebook output | **20 GB** in `/kaggle/working` (plus unsaved scratchpad disk) | Kaggle Notebooks → Adding Data Sources / Technical Specs |
| CPU notebook | 4 cores, **30 GB RAM**, 12 h general limit | Kaggle Notebooks → Technical Specs |
| Standard GPU notebook | 4 cores, 29 GB RAM | Kaggle Notebooks → Technical Specs |
| **This competition's GPU** | **NVIDIA RTX Pro 6000, 96 GB**, CPU/GPU notebook **9 h** | Competition Overview → Code Requirements |
| Startup | **15 min** (installs + model server + `Agent.__init__`) | Data tab; `kaggle_evaluation` README |
| Per-decision deadline | **90 s** (game ends at best score so far) | Data tab |
| Total game time | 32 × 10 min = **5 h 20 min** of the 9 h | Data tab |
| Submission rate | **5 per day**, team-wide | Kaggle Competitions docs; CLI confirms 5 remaining |

### Effective (practical) ceiling

- The 96 GB GPU could *hold* a ~60B Q4 model, and a 200 GB dataset could attach it — but the game advances every **200 ms** and a late reply lands at a later decision point. Latency, not storage, is the binding constraint.
- CPU fallback has only 30 GB RAM, so anything near that is out if you need to run without the GPU.
- 15 min startup includes loading weights + projector; very large files eat that budget.

| Model class | Approx. weight size (Q4 + projector) | Verdict for GGA |
| --- | --- | --- |
| 0.5B (liltii-v0.2) | ~0.5 GB | Text-only → unusable regardless of size |
| **0.8B v0.3 + mmproj** | **~718 MB** | ✅ Primary choice; fast enough for the 200 ms loop |
| **3.2B Gemma4-pruned + mmproj** | **~3.5 GB** | ✅ Attaches fine; measure latency before adopting |
| 7B Q4 + projector | ~5–7 GB | ⚠️ Feasible on the 96 GB GPU; latency must be verified |
| 13B+ Q4 | ~8 GB+ | ❌ Not worth it — too slow for real-time control |

**Rule of thumb:** keep total attached weights under ~10 GB and require p95 decision latency (including image encode) well under 1 s locally. Bigger models buy little here.

---

## 2. Rules & regulations

### 2.1 Task and submission (technical rules)

- Build **one offline agent** that plays **32 browser games across 10 genres**, 10 min each, using raw screen frames and mouse/keyboard input. Games do not pause while the agent thinks.
- **4 sample games** are public; **28 are hidden** until evaluation and send only pixels plus a brief (`description`, `controls`).
- Submission is **notebook-only**: write `/kaggle/working/agent.py` defining `Agent` with `__init__` and `step(obs, tools) -> Action`, then start `GGAInferenceServer().run()` unconditionally in the last cell. If guarded by `KAGGLE_IS_COMPETITION_RERUN`, call `run_local_gateway()` otherwise.
- **One `Agent` instance plays all 32 games**; reset per-game state at `obs.elapsed_s ≈ 0` (or same `elapsed_s` with `last_action == {}`).
- Actions must be one of 11 tools: `click`, `move`, `drag`, `scroll`, `press_key`, `hold_keys`, `key_down`, `key_up`, `wait`, `sequence` (≤200 steps), `skip`. Exceptions/unusable replies → `skip`.
- **Internet is disabled.** You may attach freely/publicly available external data, including pretrained models (Kaggle Models or your own dataset).
- You may start a localhost inference server (vLLM, **llama.cpp**, …); it counts toward the 15-min startup.
- Local runs (`gga.game`) report **no score**; real scoring happens in a Kaggle rerun (~6 h). The scoring container deliberately gives very limited error messages — test locally first.

### 2.2 Scoring and leaderboard

- Per game: `score = min(1, max(0, (value − floor) / (human − floor)))`; 0 = doing nothing, 1 = human baseline.
- Every submission plays all 32 games. **Public LB = mean of 16** (including the 4 samples). **Private LB = mean of the other 16** and decides final ranking.
- Up to **two final submissions**; the better **private** score is used.
- Games are deterministic; variation comes from agent sampling/timing (~0.001–0.01). Use deterministic settings for comparisons.
- Do not chase the public leaderboard — overfitting to it does not improve private rank.

### 2.3 Timeline, eligibility, prizes

- Start **Nov 23, 2026**; entry + team merger deadline **Feb 22, 2027**; final submission **Mar 1, 2027** (11:59 PM UTC). Host may change the timeline; check the website.
- Prizes: **$16k / $12k / $9k / $7k / $6k** (total $50k).
- Eligibility: registered Kaggle account; 18+ or age of majority; not a resident of Crimea/DNR/LNR, Cuba, Iran, North Korea; not a person/entity under U.S. export controls or sanctions. Local laws may apply; a winner in a country where prizes cannot be awarded is not prize-eligible.
- Entering as a company/institution binds both you and the entity, including employer policy compliance.
- Your account currently shows `userHasEntered: True`, 0 submissions, 5 remaining today.

### 2.4 Legal rules (Rules tab, Section C — all 18)

| # | Rule | Practical meaning |
| --- | --- | --- |
| C.1 | Eligibility | As above; false identity/residency info → disqualification. |
| C.2 | Sponsor & platform | GARC sponsors; Kaggle hosts and is not a party to sponsor agreements; Kaggle Terms of Use also apply. |
| C.3 | Competition period | Timeline may change; you are responsible for tracking deadlines/time zones. |
| C.4 | Entry | No purchase required; register before entry deadline; **no hand-labeling or human prediction of validation/test records**; late/invalid submissions void. |
| C.5 | Individuals & teams | One account per person; one team only; no private sharing outside teams; forum sharing with everyone is OK; mergers before merger deadline. |
| C.6 | Submission code | No private code sharing; **your submission code must be under an OSI license that does not limit commercial use**; pretrained models/data with incompatible licenses are exempt from that clause; commercially available software below prize cost is exempt. |
| C.7 | Winners | Ranked by metric; private LB decides; ties broken by earlier entry. |
| C.8 | Notification & DQ | Winners notified by email; must respond within 1 week; no-prize notification within 1 week of deadline; cheating/deception/harassment → disqualification; sponsor decisions final. |
| C.9 | Prizes | Subject to verification; non-compliance → DQ or 1-week remediation (including license conflicts); documents due in 2 weeks; payment ~30 days; no transfer; team prize split evenly unless agreed. |
| C.10 | Taxes | Winner pays all taxes; 1099 for U.S. residents; failure to provide documents can forfeit prize. |
| C.11 | General conditions | Comply with all applicable laws. |
| C.12 | Publicity | You grant Kaggle/sponsor a perpetual, worldwide, royalty-free license to your name/likeness in competition-related recordings. |
| C.13 | Privacy | Kaggle and sponsor may collect/transfer personal data; you have access/portability/deletion rights. |
| C.14 | Warranty & indemnity | Submission must be your original work and must not infringe third-party rights; you indemnify competition entities for breaches. |
| C.15 | Internet | Kaggle is not liable for outages/late or lost submissions. |
| C.16 | Cancel/modify/DQ | Sponsor may cancel/modify/suspend; tampering or undermining the process → DQ and possible legal action. |
| C.17 | No employment | Entry/prize is not an offer of employment; no confidential relationship is created. |
| C.18 | Definitions | "Entry" = joined/signed up/accepted rules; "Final Submission" = the one(s) used for final placement; "Competition Data" includes public and private test sets (their split is hidden). |

**Note:** the Rules tab rendered only Section C (General Competition Rules); no separate competition-specific legal section (A/B) was visible. The task-specific requirements live on the Overview/Data tabs and are captured in §2.1–2.3 above.

### 2.5 Red lines

- ❌ No hand-labeling or human prediction of validation/test data.
- ❌ No private sharing of competition code/data outside your team.
- ❌ No multiple accounts, proxy accounts, plagiarism, vote rings, or tampering with the submission process.
- ❌ No cloud/internet at inference (offline competition) — all model serving must be local.
- ❌ Do not use hidden-game information; 28 games stay hidden until evaluation.
- ⚠️ License hygiene: set an OSI license on your code; document any model license exemption (e.g., `gemma` on Gemma4-pruned).

### 2.6 Open items to verify (not stated on the pages checked)

- The exact OSI license "presented on the Competition Website" — no specific license name was shown; use a permissive one such as Apache-2.0 or MIT for submission code.
- Maximum team size — not stated on the pages checked.
- Any undisclosed competition-specific rules in A/B sections — re-check the Rules tab before final submission.

---

## 3. Sources

- Competition: https://www.kaggle.com/competitions/generalist-gaming-agent
- Data tab: https://www.kaggle.com/competitions/generalist-gaming-agent/data
- Rules tab: https://www.kaggle.com/competitions/generalist-gaming-agent/rules
- Datasets docs/limits: https://www.kaggle.com/docs/datasets
- Notebooks docs/specs: https://www.kaggle.com/docs/notebooks
- Competitions docs/FAQ: https://www.kaggle.com/docs/competitions
- Local harness: `data/gga/protocol.py`, `data/kaggle_evaluation/README.md`
