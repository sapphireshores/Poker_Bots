#pragma once
#include <cstdint>
#include <bit>
#include <array>
#include <vector>
#include <algorithm>
#include <iostream>
#include <string>

using u64 = std::uint64_t;
constexpr u64 FULL_DECK = (1ULL << 52) - 1;

inline int card_id(int rank, int suit) {
    return suit * 13 + rank;
}

inline u64 suit_slice(u64 bitboard, int suit) {
    return (bitboard >> (13 * suit)) & 0x1FFF;
}

template <class F>
inline void for_each_card(u64 mask, F&& f) {
    while (mask) {
        int idx = std::countr_zero(mask);
        f(idx);
        mask &= mask - 1;
    }
}

extern std::array<std::uint32_t, 8192> FLUSH_TABLE;
extern std::array<std::uint32_t, 50388> NONFLUSH_TABLE;

void init_evaluator_tables();
std::uint32_t combinadic_index_7(const std::array<int, 7>& sorted_ranks);
std::uint32_t eval7(u64 hand_bitboard);
void export_tables_to_python(const std::string& filepath);
void build_preflop_classes();