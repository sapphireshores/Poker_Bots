#pragma once
#include <cstdint>
#include "evaluator.hpp"

struct State {
    uint8_t street = 0;      // 0:preflop, 1:flop, 2:turn, 3:river
    uint8_t toAct = 0;       // 0:hero, 1:opp
    uint8_t raisesLeft = 4;
    uint16_t pot = 0;
    uint16_t stack[2] = {0, 0};
    uint16_t bet[2] = {0, 0};
    uint16_t lastRaise = 0;
    u64 board = 0;
    u64 flop_board = 0;
    u64 dead = 0;
};