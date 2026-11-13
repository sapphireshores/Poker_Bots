#pragma once
#include <array>
#include <cstdint>

using u64 = std::uint64_t;
constexpr u64 FULL_DECK = (1ULL << 52) - 1ULL;

extern std::array<std::uint32_t, 8192> FLUSH_TABLE;
extern std::array<std::uint32_t, 77520> NONFLUSH7_TABLE;
extern std::array<std::uint32_t, 6188> NONFLUSH5_TABLE;

void init_evaluator_tables();
std::uint32_t eval7(u64 cards);
std::uint32_t eval5(u64 cards);