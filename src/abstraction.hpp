#pragma once
#include "state.hpp"
#include <vector>
#include <cmath>
#include <algorithm>

const std::vector<uint16_t> PREFLOP_SIZES = {6, 20, 45};
const std::vector<double> POSTFLOP_FRACTIONS = {0.33, 0.66, 1.0, 1.75};

inline uint16_t snap_to_legal(double pot_fraction, const ActionContext& ctx, uint16_t current_pot, uint16_t my_stack) {
    if (!ctx.can_raise) return 0;

    double raw_target = current_pot * pot_fraction;
    uint16_t target = static_cast<uint16_t>(std::round(raw_target));
    target = std::max(ctx.min_raise, std::min(target, ctx.max_raise));

    if (target > ctx.to_call) {
        uint16_t chips_added = target - ctx.to_call;
        if (my_stack > chips_added) {
            uint16_t stack_behind = my_stack - chips_added;
            if (stack_behind < (0.3 * current_pot)) {
                return ctx.max_raise;
            }
        }
    }

    return target;
}

inline double translate_opponent_bet(double x, double A, double B) {
    if (x <= A) return 1.0;
    if (x >= B) return 0.0;
    double p_A = ((B - x) * (1.0 + A)) / ((B - A) * (1.0 + x));
    return std::clamp(p_A, 0.0, 1.0);
}