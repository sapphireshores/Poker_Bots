#include "evaluator.hpp"
#include "solver.hpp"

extern "C" {

void py_init_engine(const char* table_path) {
    (void)table_path;
    init_evaluator_tables();
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
    uint8_t to_act,
    uint8_t raises_left,
    uint16_t pot,
    uint16_t my_stack,
    uint16_t opp_stack,
    uint16_t my_bet,
    uint16_t opp_bet,
    uint16_t last_raise_size,
    uint64_t board,
    uint64_t dead,
    uint64_t opp_discard,
    const uint8_t* hole_cards,
    int num_hole_cards,
    double time_budget_ms,
    double opp_vpip,
    double opp_agg,
    double opp_fold,
    int* out_action,
    int* out_amount
) {
    State s{};
    s.street = static_cast<Street>(street);
    s.toAct = to_act;
    s.raisesLeft = raises_left;
    s.pot = pot;
    s.stack[0] = my_stack;
    s.stack[1] = opp_stack;
    s.bet[0] = my_bet;
    s.bet[1] = opp_bet;
    s.lastRaiseSize = last_raise_size;
    s.board = board;
    s.dead = dead;

    SolverResult res = solve_best_action(
        s, hole_cards, num_hole_cards, time_budget_ms,
        opp_vpip, opp_agg, opp_fold, opp_discard
    );
    *out_action = res.action;
    *out_amount = res.amount;
}

}