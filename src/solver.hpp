#pragma once
#include "state.hpp"
#include "abstraction.hpp"
#include "evaluator.hpp"

struct SolverResult {
    int action;
    int amount;
};

void init_solver_tables();

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
    double opp_sd_looseness,
    uint64_t opp_discard,
    int is_button,
    int cumulative_net,
    int score_cap
);