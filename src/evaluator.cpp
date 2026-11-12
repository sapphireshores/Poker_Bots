#include "evaluator.hpp"
#include <fstream>
#include <sstream>
#include <map>

std::array<std::uint32_t, 8192> FLUSH_TABLE{};
std::array<std::uint32_t, 50388> NONFLUSH_TABLE{};

static std::array<std::array<std::uint32_t, 8>, 25> nCr{};

static void init_ncr() {
    for (int n = 0; n < 25; ++n) {
        nCr[n][0] = 1;
        for (int k = 1; k <= std::min(n, 7); ++k) {
            nCr[n][k] = nCr[n - 1][k - 1] + nCr[n - 1][k];
        }
    }
}

std::uint32_t combinadic_index_7(const std::array<int, 7>& r) {
    std::uint32_t idx = 0;
    for (int i = 0; i < 7; ++i) {
        idx += nCr[r[i] + i][i + 1];
    }
    return idx;
}

static std::uint32_t eval5_ranks(const std::array<int, 5>& r, bool is_flush) {
    std::array<int, 5> ranks = r;
    std::sort(ranks.rbegin(), ranks.rend());

    bool is_straight = false;
    int straight_high = 0;

    if (ranks[0] - ranks[4] == 4 && ranks[0] != ranks[1] && ranks[1] != ranks[2] && ranks[2] != ranks[3] && ranks[3] != ranks[4]) {
        is_straight = true;
        straight_high = ranks[0];
    } else if (ranks[0] == 12 && ranks[1] == 3 && ranks[2] == 2 && ranks[3] == 1 && ranks[4] == 0) {
        is_straight = true;
        straight_high = 3;
    }

    if (is_straight && is_flush) return (8 << 20) | (straight_high << 16);

    std::array<int, 13> counts{};
    for (int rank : ranks) counts[rank]++;

    struct Group { int rank; int count; };
    std::vector<Group> groups;
    for (int rank = 12; rank >= 0; --rank) {
        if (counts[rank] > 0) groups.push_back({rank, counts[rank]});
    }
    std::stable_sort(groups.begin(), groups.end(), [](const Group& a, const Group& b) {
        return a.count > b.count;
    });

    if (groups[0].count == 4) return (7 << 20) | (groups[0].rank << 16) | (groups[1].rank << 12);
    if (groups[0].count == 3 && groups[1].count == 2) return (6 << 20) | (groups[0].rank << 16) | (groups[1].rank << 12);
    if (is_flush) return (5 << 20) | (ranks[0] << 16) | (ranks[1] << 12) | (ranks[2] << 8) | (ranks[3] << 4) | ranks[4];
    if (is_straight) return (4 << 20) | (straight_high << 16);
    if (groups[0].count == 3) return (3 << 20) | (groups[0].rank << 16) | (groups[1].rank << 12) | (groups[2].rank << 8);
    if (groups[0].count == 2 && groups[1].count == 2) return (2 << 20) | (groups[0].rank << 16) | (groups[1].rank << 12) | (groups[2].rank << 8);
    if (groups[0].count == 2) return (1 << 20) | (groups[0].rank << 16) | (groups[1].rank << 12) | (groups[2].rank << 8) | (groups[3].rank << 4);
    return (0 << 20) | (ranks[0] << 16) | (ranks[1] << 12) | (ranks[2] << 8) | (ranks[3] << 4) | ranks[4];
}

void init_evaluator_tables() {
    init_ncr();

    for (int mask = 0; mask < 8192; ++mask) {
        if (std::popcount((unsigned int)mask) < 5) continue;
        std::vector<int> ranks;
        for (int r = 0; r < 13; ++r) {
            if ((mask >> r) & 1) ranks.push_back(r);
        }

        std::uint32_t best_score = 0;
        int n = ranks.size();
        for (int a = 0; a < n - 4; ++a) {
            for (int b = a + 1; b < n - 3; ++b) {
                for (int c = b + 1; c < n - 2; ++c) {
                    for (int d = c + 1; d < n - 1; ++d) {
                        for (int e = d + 1; e < n; ++e) {
                            std::array<int, 5> sub = {ranks[a], ranks[b], ranks[c], ranks[d], ranks[e]};
                            best_score = std::max(best_score, eval5_ranks(sub, true));
                        }
                    }
                }
            }
        }
        FLUSH_TABLE[mask] = best_score;
    }

    for (int r0 = 0; r0 < 13; ++r0) {
    for (int r1 = r0; r1 < 13; ++r1) {
    for (int r2 = r1; r2 < 13; ++r2) {
    for (int r3 = r2; r3 < 13; ++r3) {
    for (int r4 = r3; r4 < 13; ++r4) {
    for (int r5 = r4; r5 < 13; ++r5) {
    for (int r6 = r5; r6 < 13; ++r6) {
        std::array<int, 7> multiset = {r0, r1, r2, r3, r4, r5, r6};
        std::uint32_t idx = combinadic_index_7(multiset);

        std::uint32_t best_score = 0;
        for (int a = 0; a < 3; ++a) {
            for (int b = a + 1; b < 4; ++b) {
                for (int c = b + 1; c < 5; ++c) {
                    for (int d = c + 1; d < 6; ++d) {
                        for (int e = d + 1; e < 7; ++e) {
                            std::array<int, 5> sub = {multiset[a], multiset[b], multiset[c], multiset[d], multiset[e]};
                            best_score = std::max(best_score, eval5_ranks(sub, false));
                        }
                    }
                }
            }
        }
        NONFLUSH_TABLE[idx] = best_score;
    }}}}}}}
}

std::uint32_t eval7(u64 hand_bitboard) {
    for (int s = 0; s < 4; ++s) {
        u64 m = suit_slice(hand_bitboard, s);
        if (std::popcount(m) >= 5) {
            return FLUSH_TABLE[m];
        }
    }

    std::array<int, 7> ranks{};
    int count = 0;
    for (int r = 0; r < 13; ++r) {
        for (int s = 0; s < 4; ++s) {
            if ((hand_bitboard >> card_id(r, s)) & 1ULL) {
                ranks[count++] = r;
            }
        }
    }
    return NONFLUSH_TABLE[combinadic_index_7(ranks)];
}

void export_tables_to_python(const std::string& filepath) {
    std::ofstream out(filepath);
    out << "# Auto-generated evaluation tables\n";
    out << "FLUSH_TABLE = [";
    for (size_t i = 0; i < FLUSH_TABLE.size(); ++i) {
        out << FLUSH_TABLE[i] << (i + 1 == FLUSH_TABLE.size() ? "" : ",");
    }
    out << "]\n\n";

    out << "NONFLUSH_TABLE = [";
    for (size_t i = 0; i < NONFLUSH_TABLE.size(); ++i) {
        out << NONFLUSH_TABLE[i] << (i + 1 == NONFLUSH_TABLE.size() ? "" : ",");
    }
    out << "]\n";
    out.close();
    std::cout << "[Exporter] Successfully dumped tables to " << filepath << std::endl;
}

u64 apply_suit_permutation(u64 mask, const std::vector<int>& p) {
    u64 new_mask = 0;
    for (int s = 0; s < 4; ++s) {
        u64 suit_bits = (mask >> (13 * s)) & 0x1FFF;
        new_mask |= (suit_bits << (13 * p[s]));
    }
    return new_mask;
}

u64 get_canonical_mask(u64 mask) {
    std::vector<int> p = {0, 1, 2, 3};
    u64 min_mask = ~0ULL;
    do {
        min_mask = std::min(min_mask, apply_suit_permutation(mask, p));
    } while (std::next_permutation(p.begin(), p.end()));
    return min_mask;
}

void build_preflop_classes() {
    std::map<u64, int> canonical_to_id;
    int next_id = 0;
    int total_hands = 0;

    for (int i = 0; i < 50; ++i) {
        for (int j = i + 1; j < 51; ++j) {
            for (int k = j + 1; k < 52; ++k) {
                u64 mask = (1ULL << i) | (1ULL << j) | (1ULL << k);
                u64 canonical = get_canonical_mask(mask);
                if (canonical_to_id.find(canonical) == canonical_to_id.end()) {
                    canonical_to_id[canonical] = next_id++;
                }
                total_hands++;
            }
        }
    }

    std::cout << "[Preflop] Total 3-card combinations generated: " << total_hands << std::endl;
    std::cout << "[Preflop] Unique canonical classes found: " << canonical_to_id.size() << " (Expected 1755)" << std::endl;
}