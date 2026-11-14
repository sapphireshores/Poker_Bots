# Pokerbots Engine (3-Card Flop-Discard Texas Hold'em)

Hybrid C++20 and pure-Python poker engine for 3-card flop-discard heads-up Texas Hold'em.

## Architecture
- C++20 Monte Carlo Solver (`src/solver.cpp`, `src/evaluator.cpp`, `src/bridge.cpp`): Compiled with `-O3 -flto -mpopcnt` into `python/libpoker_solver.so`. Includes a 1,755-class precomputed preflop equity table (`src/preflop_eq.inc`), two-stage unbiased flop discard evaluation, board-aware opponent range filtering, sequential early-stopping, and dynamic time-bank pacing.
- Python Interface & Bitmask Fallback (`python/bot.py`, `python/py_fallback.py`): Manages protocol I/O, opponent statistics tracking, Stage-2 score-cap protection, and automatic fallback to an O(1) bitmask pure-Python evaluator (~1.2s per 400 hands) if native shared library loading is restricted.

## Build & Run
    cd src
    g++ -std=c++20 -O3 -flto -mpopcnt -Wall -Wextra -shared -fPIC evaluator.cpp solver.cpp bridge.cpp -o ../python/libpoker_solver.so

    cd ../python
    python3 engine.py bot.py random_bot.py --seed 101
    python3 engine.py bot.py random_bot.py --stage 2 --seed 21
