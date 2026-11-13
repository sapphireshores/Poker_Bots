#include "solver.hpp"
#include <chrono>
#include <cmath>
#include <algorithm>

#ifndef ITER_CAP_DISCARD
#define ITER_CAP_DISCARD 8000
#endif
#ifndef ITER_CAP_ACTION
#define ITER_CAP_ACTION 10000
#endif

struct FastRNG {
    uint64_t s;
    FastRNG(uint64_t seed) {
        uint64_t now_ns = static_cast<uint64_t>(
            std::chrono::steady_clock::now().time_since_epoch().count()
        );
        s = seed ^ (now_ns * 0x9E3779B97F4A7C15ULL);
        if (s == 0) s = 0x9E3779B97F4A7C15ULL;
    }
    inline uint64_t next() {
        s ^= s >> 12;
        s ^= s << 25;
        s ^= s >> 27;
        return s * 0x2545F4914F6CDD1DULL;
    }
    inline int next_int(int max_val) {
        return static_cast<int>(next() % static_cast<uint64_t>(max_val));
    }
    inline double next_double() {
        return (next() >> 11) * (1.0 / 9007199254740992.0);
    }
};

static inline u64 sample_cards(u64& available_mask, int k, FastRNG& rng) {
    u64 chosen = 0;
    int avail_count = std::popcount(available_mask);
    for (int i = 0; i < k && avail_count > 0; ++i) {
        int target = rng.next_int(avail_count);
        u64 temp = available_mask;
        while (target > 0) {
            temp &= (temp - 1);
            --target;
        }
        int card_idx = std::countr_zero(temp);
        u64 bit = (1ULL << card_idx);
        chosen |= bit;
        available_mask &= ~bit;
        --avail_count;
    }
    return chosen;
}

static inline int two_card_strength(int a, int b) {
    int ra = a % 13, sa = a / 13;
    int rb = b % 13, sb = b / 13;
    int hi = std::max(ra, rb), lo = std::min(ra, rb);
    int score = hi * 20 + lo * 10;
    if (ra == rb) score += 200 + ra * 15;
    if (sa == sb) score += 28;
    if (hi - lo == 1) score += 18;
    else if (hi - lo == 2) score += 10;
    return score;
}

static inline u64 best_two_of_three(const uint8_t h[3]) {
    int best_drop = 2;
    int best_score = -100000;
    for (int drop = 0; drop < 3; ++drop) {
        int a = -1, b = -1;
        for (int i = 0; i < 3; ++i) {
            if (i == drop) continue;
            if (a == -1) a = h[i];
            else b = h[i];
        }
        int score = two_card_strength(a, b);
        if (score > best_score) {
            best_score = score;
            best_drop = drop;
        }
    }
    u64 mask = 0;
    for (int i = 0; i < 3; ++i) {
        if (i != best_drop) mask |= (1ULL << h[i]);
    }
    return mask;
}

// Board-aware 2-of-3 selection on the flop using 5-card evaluator + preflop tie-breaker
static inline u64 best_two_on_flop(const uint8_t h[3], u64 flop_mask) {
    int best_drop = 2;
    int64_t best_val = -1;
    for (int drop = 0; drop < 3; ++drop) {
        int a = -1, b = -1;
        u64 pair_mask = 0;
        for (int i = 0; i < 3; ++i) {
            if (i == drop) continue;
            pair_mask |= (1ULL << h[i]);
            if (a == -1) a = h[i];
            else b = h[i];
        }
        // Evaluate actual 5-card flop strength + subtle draw/high-card tie-breaker
        int64_t val = (static_cast<int64_t>(eval7(flop_mask | pair_mask)) << 12)
                    + two_card_strength(a, b);
        if (val > best_val) {
            best_val = val;
            best_drop = drop;
        }
    }
    u64 mask = 0;
    for (int i = 0; i < 3; ++i) {
        if (i != best_drop) mask |= (1ULL << h[i]);
    }
    return mask;
}

int solve_best_discard(
    const uint8_t hole_cards[3],
    const uint8_t board_cards[3],
    uint64_t dead_mask,
    double time_budget_ms
) {
    auto start_time = std::chrono::steady_clock::now();
    FastRNG rng(0x123456789ABCDEFULL ^ dead_mask ^ (hole_cards[0] * 131 + hole_cards[1] * 17 + hole_cards[2]));

    u64 board_mask = 0;
    for (int i = 0; i < 3; ++i) board_mask |= (1ULL << board_cards[i]);

    u64 full_hole = (1ULL << hole_cards[0]) | (1ULL << hole_cards[1]) | (1ULL << hole_cards[2]);
    u64 base_dead = dead_mask | board_mask | full_hole;

    double wins[3] = {0.0, 0.0, 0.0};
    int iterations = 0;

    while (iterations < ITER_CAP_DISCARD) {
        if ((iterations & 127) == 0) {
            auto now = std::chrono::steady_clock::now();
            double elapsed = std::chrono::duration<double, std::milli>(now - start_time).count();
            if (elapsed >= time_budget_ms) break;
        }

        u64 avail = FULL_DECK & ~base_dead;
        uint8_t opp_h[3];
        for (int i = 0; i < 3; ++i) {
            u64 c = sample_cards(avail, 1, rng);
            opp_h[i] = static_cast<uint8_t>(std::countr_zero(c));
        }
        // Board-aware opponent keep on the flop
        u64 opp_kept = best_two_on_flop(opp_h, board_mask);
        u64 runout = sample_cards(avail, 2, rng);

        u64 full_board = board_mask | runout;
        uint32_t opp_score = eval7(full_board | opp_kept);

        for (int d = 0; d < 3; ++d) {
            u64 my_kept = full_hole & ~(1ULL << hole_cards[d]);
            uint32_t my_score = eval7(full_board | my_kept);
            if (my_score > opp_score) wins[d] += 1.0;
            else if (my_score == opp_score) wins[d] += 0.5;
        }
        ++iterations;
    }

    int best_discard = 0;
    if (wins[1] > wins[best_discard]) best_discard = 1;
    if (wins[2] > wins[best_discard]) best_discard = 2;
    return best_discard;
}

SolverResult solve_best_action(
    const State& root_state,
    const uint8_t my_hole[3],
    int num_hole_cards,
    double time_budget_ms,
    double opp_vpip,
    double opp_agg,
    double opp_fold,
    uint64_t opp_discard
) {
    auto start_time = std::chrono::steady_clock::now();
    ActionContext ctx = get_action_context(root_state);

    u64 my_hole_mask = 0;
    for (int i = 0; i < num_hole_cards; ++i) {
        my_hole_mask |= (1ULL << my_hole[i]);
    }

    int board_count = std::popcount(root_state.board);
    int needed_board = std::max(0, 5 - board_count);
    u64 base_dead = root_state.dead | root_state.board | my_hole_mask;

    // Candidate keeps: if holding 3 cards on flop, evaluate all 3 keeps on common samples
    u64 cand[3] = {0, 0, 0};
    int ncand = 1;
    if (num_hole_cards == 3) {
        if (board_count >= 3) {
            ncand = 3;
            for (int d = 0; d < 3; ++d) cand[d] = my_hole_mask & ~(1ULL << my_hole[d]);
        } else {
            cand[0] = best_two_of_three(my_hole);
        }
    } else {
        cand[0] = my_hole_mask;
    }
    u64 eval_hole = cand[0];

    double pot = std::max<double>(2.0, root_state.pot);
    double to_call = static_cast<double>(ctx.to_call);
    // Correct pre-bet pot denominator (pot already includes to_call)
    double bet_fraction = to_call / std::max(2.0, pot - to_call);

    bool is_maniac = (opp_agg > 0.45);
    bool is_overfolder = (opp_fold > 0.55);
    bool is_station = (opp_vpip > 0.72 && opp_fold < 0.30);

    int min_opp_preflop_score = 0;
    if (!is_maniac && to_call > 0.0) {
        if (bet_fraction >= 0.75) min_opp_preflop_score = 210;
        else if (bet_fraction >= 0.35) min_opp_preflop_score = 165;
        else if (board_count > 0) min_opp_preflop_score = 130;
    }

    FastRNG rng(0xCAFEBABE12345678ULL ^ eval_hole ^ root_state.board ^ (root_state.pot * 997ULL));
    double eq_sum[3] = {0.0, 0.0, 0.0};
    int iterations = 0;
    int opp_d = (opp_discard != 0) ? std::countr_zero(opp_discard) : -1;

    while (iterations < ITER_CAP_ACTION) {
        if ((iterations & 127) == 0) {
            auto now = std::chrono::steady_clock::now();
            double elapsed = std::chrono::duration<double, std::milli>(now - start_time).count();
            if (elapsed >= time_budget_ms) break;
        }

        u64 avail = FULL_DECK & ~base_dead;
        u64 opp_hole = 0;

        for (int attempt = 0; attempt < 24; ++attempt) {
            u64 temp_avail = avail;
            u64 kept = 0;
            if (opp_d >= 0) {
                // Post-discard: opponent kept pair preferred over (card, opp_d)
                kept = sample_cards(temp_avail, 2, rng);
                int c1 = std::countr_zero(kept);
                int c2 = std::countr_zero(kept & (kept - 1));
                int s12 = two_card_strength(c1, c2);
                if (s12 < two_card_strength(c1, opp_d) || s12 < two_card_strength(c2, opp_d)) {
                    if (attempt < 23) continue;
                }
            } else if (num_hole_cards == 3) {
                // Pre-discard: opponent also holds 3 cards and keeps best 2
                u64 three = sample_cards(temp_avail, 3, rng);
                uint8_t h3[3];
                int k = 0;
                u64 t = three;
                while (t) {
                    h3[k++] = static_cast<uint8_t>(std::countr_zero(t));
                    t &= (t - 1);
                }
                kept = (board_count >= 3) ? best_two_on_flop(h3, root_state.board) : best_two_of_three(h3);
            } else {
                kept = sample_cards(temp_avail, 2, rng);
            }

            int c1 = std::countr_zero(kept);
            int c2 = std::countr_zero(kept & (kept - 1));
            if (two_card_strength(c1, c2) >= min_opp_preflop_score || attempt == 23) {
                opp_hole = kept;
                avail = temp_avail;
                break;
            }
        }

        u64 runout = sample_cards(avail, needed_board, rng);
        u64 final_board = root_state.board | runout;
        uint32_t opp_score = eval7(final_board | opp_hole);
        for (int c = 0; c < ncand; ++c) {
            uint32_t my_score = eval7(final_board | cand[c]);
            if (my_score > opp_score) eq_sum[c] += 1.0;
            else if (my_score == opp_score) eq_sum[c] += 0.5;
        }
        ++iterations;
    }

    double equity_sum = eq_sum[0];
    for (int c = 1; c < ncand; ++c) equity_sum = std::max(equity_sum, eq_sum[c]);
    double equity = (iterations > 0) ? (equity_sum / iterations) : 0.5;
    double jitter = (rng.next_double() - 0.5) * 0.24;

    // 1. Facing a bet / raise (to_call > 0)
    if (to_call > 0.0) {
        double pot_odds = to_call / (pot + to_call);

        // Value raise strong hands (size up aggressively vs calling stations)
        double raise_thresh = is_station ? 0.57 : 0.64;
        if (ctx.can_raise && equity >= raise_thresh) {
            double base_mult = (equity >= 0.78) ? 1.0 : 0.68;
            if (is_station) base_mult += 0.25;
            double mult = std::max(0.45, base_mult + jitter);
            uint16_t target = static_cast<uint16_t>(root_state.bet[1] + pot * mult);
            uint16_t raise_to = std::max(ctx.min_raise, std::min(ctx.max_raise, target));
            return {RAISE, raise_to};
        }

        // Semi-bluff check-raise / re-raise against over-folders
        if (ctx.can_raise && is_overfolder && !is_maniac && equity >= 0.45 && equity < 0.56 && (rng.next_int(100) < 28)) {
            double mult = std::max(0.40, 0.55 + jitter);
            uint16_t target = static_cast<uint16_t>(root_state.bet[1] + pot * mult);
            uint16_t raise_to = std::max(ctx.min_raise, std::min(ctx.max_raise, target));
            return {RAISE, raise_to};
        }

        double safety_margin = 0.04 + 0.08 * std::min(1.5, bet_fraction);

        if (is_maniac) {
            safety_margin -= 0.06;
            if (equity >= 0.55) return {CALL, 0};
        }

        if (opp_agg < 0.12 && bet_fraction > 0.8) {
            safety_margin += 0.06;
        }

        // Positional preflop open-raise from Button (SB, my_bet == 1, opp_bet == 2)
        if (board_count == 0 && root_state.bet[0] == 1 && root_state.bet[1] == 2) {
            if (ctx.can_raise && (equity >= 0.47 || (is_overfolder && equity >= 0.41))) {
                uint16_t open_to = std::max<uint16_t>(ctx.min_raise, std::min<uint16_t>(ctx.max_raise, 6));
                return {RAISE, open_to};
            }
            if (equity >= 0.38) {
                return {CALL, 0};
            }
        }

        if (equity >= pot_odds + safety_margin) {
            return {CALL, 0};
        }

        return {FOLD, 0};
    }

    // 2. Free to check (to_call == 0)
    if (ctx.can_raise) {
        // Pot control on Turn (board_count == 4): check back medium pairs (unless vs station)
        if (board_count == 4 && equity >= 0.54 && equity < 0.62 && !is_station) {
            return {CALL, 0};
        }

        double value_thresh = is_station ? 0.50 : 0.58;
        if (equity >= value_thresh) {
            double base_frac = (equity >= 0.75) ? 0.85 : 0.55;
            if (is_station) base_frac += 0.25; // Punish calling stations with larger value bets
            double frac = std::max(0.33, base_frac + jitter);
            uint16_t bet_amt = snap_to_legal(frac, ctx, static_cast<uint16_t>(pot), root_state.stack[0]);
            if (bet_amt >= ctx.min_raise) {
                return {RAISE, bet_amt};
            }
        }

        // Polarized bluff frequency
        int bluff_pct = 22;
        if (is_station || is_maniac) bluff_pct = 0;
        else if (is_overfolder) bluff_pct = 45;

        if (equity >= 0.44 && (rng.next_int(100) < bluff_pct)) {
            double frac = std::max(0.28, 0.36 + jitter * 0.5);
            uint16_t bet_amt = snap_to_legal(frac, ctx, static_cast<uint16_t>(pot), root_state.stack[0]);
            if (bet_amt >= ctx.min_raise) {
                return {RAISE, bet_amt};
            }
        }
    }

    return {CALL, 0};
}