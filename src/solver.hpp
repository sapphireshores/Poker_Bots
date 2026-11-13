#pragma once
#include <cstdint>
#include <algorithm>
#include "state.hpp"

enum ActionType {
    FOLD = 0,
    CALL = 1,
    RAISE = 2
};

struct ActionContext {
    bool can_fold = false;
    bool can_check = false;
    bool can_call = false;
    bool can_raise = false;
    uint16_t to_call = 0;
    uint16_t min_raise = 0;
    uint16_t max_raise = 0;
};

inline ActionContext get_action_context(const State& st) {
    ActionContext ctx{};
    uint16_t my_bet = st.bet[0];
    uint16_t opp_bet = st.bet[1];
    uint16_t my_stack = st.stack[0];
    uint16_t opp_stack = st.stack[1];

    ctx.to_call = (opp_bet > my_bet) ? static_cast<uint16_t>(opp_bet - my_bet) : 0;
    ctx.can_fold = (ctx.to_call > 0);
    ctx.can_check = (ctx.to_call == 0);
    ctx.can_call = (ctx.to_call > 0 && my_stack > 0);

    uint16_t max_total = static_cast<uint16_t>(my_bet + std::min<uint32_t>(my_stack, static_cast<uint32_t>(ctx.to_call) + opp_stack));
    uint16_t min_inc = std::max<uint16_t>(2, st.lastRaise);
    uint16_t min_total = static_cast<uint16_t>(opp_bet + min_inc);

    if (st.raisesLeft > 0 && my_stack > ctx.to_call && opp_stack > 0 && max_total > opp_bet) {
        ctx.can_raise = true;
        ctx.min_raise = std::min(min_total, max_total);
        ctx.max_raise = max_total;
    }
    return ctx;
}

#include "abstraction.hpp"

struct SolverResult {
    int best_action;
    uint16_t raise_amount;
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
    double opp_fold_pre,
    double opp_fold_post,
    double opp_sd_looseness,
    uint64_t opp_discard,
    int is_button,
    int opp_raised,
    int cumulative_net,
    int score_cap
);