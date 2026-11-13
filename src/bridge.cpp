#include "evaluator.hpp"
#include "solver.hpp"
#include "state.hpp"
#include <cstdint>

extern "C" {

void py_init_engine(const char* /*bin_path*/) {
    init_evaluator_tables();
    init_solver_tables();
}

int py_choose_discard(
    const uint8_t* hole_cards,
    const uint8_t* board_cards,
    uint64_t dead_mask,
    double time_budget_ms
) {
    return solve_best_discard(hole_cards, board_cards, dead_mask, time_budget_ms);
}

void py_choose_action(
    uint8_t street,
    uint8_t toAct,
    uint8_t raisesLeft,
    uint16_t pot,
    uint16_t my_stack,
    uint16_t opp_stack,
    uint16_t my_bet,
    uint16_t opp_bet,
    uint16_t lastRaise,
    uint64_t board,
    uint64_t flop_board,
    uint64_t dead,
    uint64_t opp_discard,
    const uint8_t* my_hole,
    int num_hole_cards,
    double time_budget_ms,
    double opp_vpip,
    double opp_agg,
    double opp_fold_pre,
    double opp_fold_post,
    double opp_sd_looseness,
    int is_button,
    int opp_raised,
    int cumulative_net,
    int score_cap,
    int* out_action,
    int* out_amount
) {
    State st{};
    st.street = street;
    st.toAct = toAct;
    st.raisesLeft = raisesLeft;
    st.pot = pot;
    st.stack[0] = my_stack;
    st.stack[1] = opp_stack;
    st.bet[0] = my_bet;
    st.bet[1] = opp_bet;
    st.lastRaise = lastRaise;
    st.board = board;
    st.flop_board = flop_board;
    st.dead = dead;

    SolverResult res = solve_best_action(
        st, my_hole, num_hole_cards, time_budget_ms,
        opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_looseness,
        opp_discard, is_button, opp_raised, cumulative_net, score_cap
    );

    *out_action = res.best_action;
    *out_amount = static_cast<int>(res.raise_amount);
}

}