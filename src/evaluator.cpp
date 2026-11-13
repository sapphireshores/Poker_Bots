#include "evaluator.hpp"
#include <algorithm>
#include <bit>

std::array<std::uint32_t, 8192> FLUSH_TABLE{};
std::array<std::uint32_t, 77520> NONFLUSH7_TABLE{};
std::array<std::uint32_t, 6188> NONFLUSH5_TABLE{};

static std::uint32_t NCR[22][8]{};
static bool TABLES_INIT = false;

static void init_ncr() {
    for (int n = 0; n < 22; ++n) {
        NCR[n][0] = 1;
        for (int k = 1; k < 8 && k <= n; ++k) {
            NCR[n][k] = NCR[n - 1][k - 1] + NCR[n - 1][k];
        }
    }
}

static inline std::uint32_t combinadic_index_7(const std::uint8_t r[7]) {
    std::uint32_t idx = 0;
    for (int i = 0; i < 7; ++i) {
        idx += NCR[r[i] + i][i + 1];
    }
    return idx;
}

static inline std::uint32_t combinadic_index_5(const std::uint8_t r[5]) {
    std::uint32_t idx = 0;
    for (int i = 0; i < 5; ++i) {
        idx += NCR[r[i] + i][i + 1];
    }
    return idx;
}

static std::uint32_t eval5_ranks(const std::array<std::uint8_t, 5>& sorted_r, bool is_flush) {
    int cnt[13]{};
    for (std::uint8_t r : sorted_r) ++cnt[r];

    std::uint16_t mask = 0;
    for (int r = 0; r < 13; ++r) {
        if (cnt[r]) mask |= (1U << r);
    }

    int straight_hi = -1;
    if (std::popcount(mask) == 5) {
        if (mask == 0x100FU) {
            straight_hi = 3; // A-2-3-4-5 wheel
        } else {
            int lo = std::countr_zero(mask);
            if ((mask >> lo) == 0x1FU) straight_hi = lo + 4;
        }
    }

    if (is_flush && straight_hi >= 0) {
        return (8U << 20) | static_cast<std::uint32_t>(straight_hi);
    }

    int quad = -1, trip = -1, p1 = -1, p2 = -1;
    std::uint32_t kickers = 0;
    for (int r = 12; r >= 0; --r) {
        if (cnt[r] == 4) quad = r;
        else if (cnt[r] == 3) trip = r;
        else if (cnt[r] == 2) {
            if (p1 < 0) p1 = r;
            else p2 = r;
        } else if (cnt[r] == 1) {
            kickers = (kickers << 4) | static_cast<std::uint32_t>(r);
        }
    }

    if (quad >= 0) return (7U << 20) | (static_cast<std::uint32_t>(quad) << 4) | kickers;
    if (trip >= 0 && p1 >= 0) return (6U << 20) | (static_cast<std::uint32_t>(trip) << 4) | static_cast<std::uint32_t>(p1);
    if (is_flush) return (5U << 20) | kickers;
    if (straight_hi >= 0) return (4U << 20) | static_cast<std::uint32_t>(straight_hi);
    if (trip >= 0) return (3U << 20) | (static_cast<std::uint32_t>(trip) << 8) | kickers;
    if (p1 >= 0 && p2 >= 0) return (2U << 20) | (static_cast<std::uint32_t>(p1) << 8) | (static_cast<std::uint32_t>(p2) << 4) | kickers;
    if (p1 >= 0) return (1U << 20) | (static_cast<std::uint32_t>(p1) << 12) | kickers;
    return kickers;
}

static void init_flush() {
    for (std::uint16_t m = 0; m < 8192; ++m) {
        if (std::popcount(m) < 5) continue;
        std::uint32_t best = 0;
        std::uint8_t present[13];
        int n = 0;
        for (int r = 0; r < 13; ++r) {
            if (m & (1U << r)) present[n++] = static_cast<std::uint8_t>(r);
        }
        for (int a = 0; a < n - 4; ++a)
            for (int b = a + 1; b < n - 3; ++b)
                for (int c = b + 1; c < n - 2; ++c)
                    for (int d = c + 1; d < n - 1; ++d)
                        for (int e = d + 1; e < n; ++e) {
                            std::array<std::uint8_t, 5> hand{present[a], present[b], present[c], present[d], present[e]};
                            best = std::max(best, eval5_ranks(hand, true));
                        }
        FLUSH_TABLE[m] = best;
    }
}

static void init_nonflush7() {
    std::array<std::uint8_t, 7> ms{};
    for (std::uint8_t r0 = 0; r0 < 13; ++r0) {
        ms[0] = r0;
        for (std::uint8_t r1 = r0; r1 < 13; ++r1) {
            ms[1] = r1;
            for (std::uint8_t r2 = r1; r2 < 13; ++r2) {
                ms[2] = r2;
                for (std::uint8_t r3 = r2; r3 < 13; ++r3) {
                    ms[3] = r3;
                    for (std::uint8_t r4 = r3; r4 < 13; ++r4) {
                        ms[4] = r4;
                        for (std::uint8_t r5 = r4; r5 < 13; ++r5) {
                            ms[5] = r5;
                            for (std::uint8_t r6 = r5; r6 < 13; ++r6) {
                                ms[6] = r6;
                                if (r0 == r4 || r1 == r5 || r2 == r6) continue; // >4 of same rank impossible
                                std::uint32_t best = 0;
                                for (int skip1 = 0; skip1 < 6; ++skip1) {
                                    for (int skip2 = skip1 + 1; skip2 < 7; ++skip2) {
                                        std::array<std::uint8_t, 5> h{};
                                        int idx = 0;
                                        for (int k = 0; k < 7; ++k) {
                                            if (k != skip1 && k != skip2) h[idx++] = ms[k];
                                        }
                                        best = std::max(best, eval5_ranks(h, false));
                                    }
                                }
                                NONFLUSH7_TABLE[combinadic_index_7(ms.data())] = best;
                            }
                        }
                    }
                }
            }
        }
    }
}

static void init_nonflush5() {
    std::array<std::uint8_t, 5> ms{};
    for (std::uint8_t r0 = 0; r0 < 13; ++r0) {
        ms[0] = r0;
        for (std::uint8_t r1 = r0; r1 < 13; ++r1) {
            ms[1] = r1;
            for (std::uint8_t r2 = r1; r2 < 13; ++r2) {
                ms[2] = r2;
                for (std::uint8_t r3 = r2; r3 < 13; ++r3) {
                    ms[3] = r3;
                    for (std::uint8_t r4 = r3; r4 < 13; ++r4) {
                        ms[4] = r4;
                        if (r0 == r4) continue; // 5 of same rank impossible
                        NONFLUSH5_TABLE[combinadic_index_5(ms.data())] = eval5_ranks(ms, false);
                    }
                }
            }
        }
    }
}

void init_evaluator_tables() {
    if (TABLES_INIT) return;
    init_ncr();
    init_flush();
    init_nonflush7();
    init_nonflush5();
    TABLES_INIT = true;
}

std::uint32_t eval7(u64 cards) {
    for (int s = 0; s < 4; ++s) {
        std::uint16_t slice = static_cast<std::uint16_t>((cards >> (s * 13)) & 0x1FFFULL);
        if (std::popcount(slice) >= 5) {
            return FLUSH_TABLE[slice];
        }
    }
    std::uint8_t ranks[7];
    int k = 0;
    for (int r = 0; r < 13; ++r) {
        for (int s = 0; s < 4; ++s) {
            if (cards & (1ULL << (s * 13 + r))) {
                ranks[k++] = static_cast<std::uint8_t>(r);
            }
        }
    }
    return NONFLUSH7_TABLE[combinadic_index_7(ranks)];
}

std::uint32_t eval5(u64 cards) {
    for (int s = 0; s < 4; ++s) {
        std::uint16_t slice = static_cast<std::uint16_t>((cards >> (s * 13)) & 0x1FFFULL);
        if (std::popcount(slice) == 5) {
            return FLUSH_TABLE[slice];
        }
    }
    std::uint8_t ranks[5];
    int k = 0;
    for (int r = 0; r < 13; ++r) {
        for (int s = 0; s < 4; ++s) {
            if (cards & (1ULL << (s * 13 + r))) {
                ranks[k++] = static_cast<std::uint8_t>(r);
            }
        }
    }
    return NONFLUSH5_TABLE[combinadic_index_5(ranks)];
}