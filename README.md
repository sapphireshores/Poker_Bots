# Poker_Bots

Autonomous heads-up poker bot built with a C++20 Monte Carlo equity solver and a Python stdin/stdout controller.

## Project Structure

- `python/bot.py` — Main bot entrypoint. Handles JSON stdin/stdout communication, enforces legal action/discard constraints, tracks the 60s time bank, and maintains an online Bayesian opponent profile (VPIP, raise aggression, fold-to-bet).
- `python/libpoker_solver.so` — Precompiled shared library loaded via Python's built-in `ctypes` module.
- `src/evaluator.hpp`, `src/evaluator.cpp` — 52-bit bitboard representation and 7-card combinadic hand evaluator (`FLUSH_TABLE` / `NONFLUSH_TABLE`).
- `src/solver.hpp`, `src/solver.cpp` — Time-budgeted Monte Carlo equity and flop-discard engine with range-conditioned opponent sampling, positional preflop adjustments (Button vs. BB), turn pot-control, and bet-size jitter.
- `src/state.hpp`, `src/abstraction.hpp` — Game state tracking, 4-bet cap logic, and bet-sizing quantization.
- `src/bridge.cpp` — `extern "C"` bindings between C++20 and `bot.py`.

## Runtime Notes

- Runs on standard Python 3.11+ (`ctypes`, `json`, `sys`, `os`, `gc`, `time`) with no external pip packages.
- Makes zero filesystem writes and zero network calls (compatible with read-only containers).

## Building from Source

If `libpoker_solver.so` needs to be recompiled on Linux:

```bash
cd src
g++ -std=c++20 -O3 -shared -fPIC evaluator.cpp solver.cpp bridge.cpp -o ../python/libpoker_solver.so
