#pragma once
#include <cstdint>
#include <algorithm>

enum Street : uint8_t { PRE, FLOP, DISCARD, TURN, RIVER, SHOWDOWN };
enum ActionType : uint8_t { FOLD, CALL, RAISE };

struct State {
    uint64_t hash;
    uint64_t board;
    uint64_t dead;
    uint64_t hole[2];

    uint16_t pot;
    uint16_t stack[2];
    uint16_t bet[2];
    uint16_t lastRaiseSize;

    Street street;
    uint8_t toAct;
    uint8_t raisesLeft;
    bool acted[2];
};

struct ActionContext {
    bool can_fold;
    bool can_check;
    bool can_call;
    bool can_raise;
    uint16_t min_raise;
    uint16_t max_raise;
    uint16_t to_call;
};

inline ActionContext get_action_context(const State& state) {
    ActionContext ctx = {false, false, false, false, 0, 0, 0};

    uint8_t me = state.toAct;
    uint8_t opp = me ^ 1;

    uint16_t my_bet = state.bet[me];
    uint16_t opp_bet = state.bet[opp];

    ctx.to_call = (opp_bet > my_bet) ? (opp_bet - my_bet) : 0;
    ctx.can_fold = (ctx.to_call > 0);
    ctx.can_check = (ctx.to_call == 0);
    ctx.can_call = (ctx.to_call > 0);

    ctx.max_raise = std::min<uint16_t>(my_bet + state.stack[me], opp_bet + state.stack[opp]);

    if (state.raisesLeft > 0 && ctx.max_raise > opp_bet) {
        ctx.can_raise = true;
        uint16_t step = std::max<uint16_t>(2, state.lastRaiseSize);
        ctx.min_raise = opp_bet + step;
        if (ctx.min_raise > ctx.max_raise) {
            ctx.min_raise = ctx.max_raise;
        }
    }

    return ctx;
}

inline void apply_action(State& state, ActionType action, uint16_t amount = 0) {
    uint8_t me = state.toAct;
    uint8_t opp = me ^ 1;

    state.acted[me] = true;

    if (action == FOLD) {
        state.street = SHOWDOWN;
        return;
    } else if (action == CALL) {
        uint16_t to_call = std::min<uint16_t>(state.stack[me], state.bet[opp] - state.bet[me]);
        state.stack[me] -= to_call;
        state.bet[me] += to_call;
    } else if (action == RAISE) {
        uint16_t to_add = amount - state.bet[me];
        state.stack[me] -= to_add;
        state.lastRaiseSize = amount - state.bet[opp];
        state.bet[me] = amount;
        state.raisesLeft--;
    }

    bool bets_matched = (state.bet[0] == state.bet[1]);
    bool someone_all_in = (state.stack[0] == 0 || state.stack[1] == 0);
    bool both_acted = (state.acted[0] && state.acted[1]);

    if ((bets_matched || someone_all_in) && both_acted) {
        state.pot += state.bet[0] + state.bet[1];
        state.bet[0] = 0;
        state.bet[1] = 0;

        state.acted[0] = false;
        state.acted[1] = false;
        state.raisesLeft = 4;
        state.lastRaiseSize = 0;
        state.toAct = 0;

        if (state.street == PRE) state.street = FLOP;
        else if (state.street == FLOP) state.street = DISCARD;
        else if (state.street == DISCARD) state.street = TURN;
        else if (state.street == TURN) state.street = RIVER;
        else if (state.street == RIVER) state.street = SHOWDOWN;
    } else {
        state.toAct = opp;
    }
}