#pragma once
#include "state.hpp"
#include "abstraction.hpp"
#include "evaluator.hpp"

struct SolverResult {
    int action;
    int amount;
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
    double opp_vpip,
    double opp_agg,
    double opp_fold,
    uint64_t opp_discard
);