# Discard Hold'em Bot — Pokerbots

Autonomous heads-up Discard Hold'em agent built in pure Python 3.11 standard library (`bot.py`).

## Repository Structure
- `bot.py` — Self-contained bot (pure Python 3.11 stdlib, zero external dependencies).
- `engine.py` — Local duplicate-deal match runner for testing.
- `random_bot.py` — Baseline random agent for local benchmarking.
- `src/` — Offline C++ reference evaluator and solver prototypes.

## Architecture & Strategy
- **7-Card Bitmask Hand Evaluator**: Fast bit-twiddling 5-card and 7-card evaluator (`_eval5_fast`, `_eval7_fast`) using precomputed 13-bit rank masks (`_STRAIGHT_HI`, `_TOP5_VAL`).
- **Precomputed 3-Card Preflop LUT**: Canonicalized 1,755-entry 3-card preflop equity table compressed with `zlib` + `base64` and unpacked once during `init`.
- **Discard-Conditioned Range Filtering**: Updates opponent hand-range weights (`_pair_range_weight`) using the public exposed flop discard (`discard_result`), bet sizing, and opponent tightness.
- **Exact Turn & River Enumeration**: Sweeps all 44 river runouts on the turn and all $\binom{43}{2} = 903$ opponent hole-card combinations on the river for zero-noise endgame equity.
- **Online Opponent Adaptation (`OpponentTracker`)**: Tracks live VPIP, aggression frequency, preflop/postflop fold-to-bet rates, and showdown looseness to exploit TAG, LAG, Calling Station, and Nit tendencies.
- **Blocker-Aware River Bluffing & Polarized Sizing**: Overbets near-nutted river hands (`equity >= 0.86`) and restricts river bluffs to missed draws holding Ace blockers while preserving medium showdown value.
- **Time-Bank & Protocol Resilience**: Dynamic per-hand millisecond budgeting with automatic panic-mode heuristic fallback (`< 350 ms`), strict `legal_actions` bounds clamping, and `_emergency_reply` crash protection.

## Local Testing
```bash
# Stage 1 (400 hands / 200 duplicate deals)
python3 engine.py bot.py random_bot.py --seed 101

# Stage 2 (1000 hands / 500 duplicate deals)
python3 engine.py bot.py random_bot.py --stage 2 --seed 21