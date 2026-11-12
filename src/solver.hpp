#pragma once
#include <cstdint>
#include "evaluator.hpp"
#include "state.hpp"
#include "abstraction.hpp"
#include "flatmap.hpp"

struct SolverResult {
    int action; // 0 = FOLD, 1 = CALL/CHECK, 2 = RAISE
    int amount; // total wager amount if RAISE
};

int solve_best_discard(
    const uint8_t hole_cards[3],
    const uint8_t board_cards[3],
    uint64_t dead_mask,
    double time_budget_ms
);

SolverResult solve_best_action(
    const State& root_state,
    const uint8_t my_hole[3],
    int num_hole_cards,
    double time_budget_ms,
    double opp_vpip = 0.55,
    double opp_agg = 0.25,
    double opp_fold = 0.40
);