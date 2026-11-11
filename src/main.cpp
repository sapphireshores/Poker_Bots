#include "evaluator.hpp"
#include <chrono>
#include <string>
#include <stdexcept>

// Helper to convert card strings like "Td", "Ah" to bitboard
u64 card_mask(const std::string& card_str) {
    std::string ranks = "23456789TJQKA";
    std::string suits = "shdc";
    
    int rank = ranks.find(card_str[0]);
    int suit = suits.find(card_str[1]);
    
    if (rank == std::string::npos || suit == std::string::npos) {
        throw std::invalid_argument("Invalid card string: " + card_str);
    }
    return 1ULL << card_id(rank, suit);
}

u64 hand_mask(const std::vector<std::string>& cards) {
    u64 mask = 0;
    for (const auto& c : cards) {
        mask |= card_mask(c);
    }
    return mask;
}

void run_validation_tests() {
    std::cout << "[Validation] Running Problem Statement test cases..." << std::endl;

    // Example 1 from Problem Statement:
    // Board: Td, 9c, 2s, 3c, 4h
    // Player A keeps: Qh, Jh (Queen-high Flush)
    // Player B keeps: 9s, 9h (Three Nines)
    u64 board = hand_mask({"Td", "9c", "2s", "3c", "4h"});
    u64 hand_A = board | hand_mask({"Qh", "Jh"});
    u64 hand_B = board | hand_mask({"9s", "9h"});

    std::uint32_t score_A = eval7(hand_A);
    std::uint32_t score_B = eval7(hand_B);

    if (score_A > score_B) {
        std::cout << "  [PASS] Ex. 1: Queen-high Flush (" << score_A << ") beats Trip 9s (" << score_B << ")" << std::endl;
    } else {
        std::cerr << "  [FAIL] Ex. 1: Evaluator returned incorrect winner! (A: " << score_A << ", B: " << score_B << ")" << std::endl;
    }

    // Example 5 Kicker check:
    // Board: Ah, Kh, 8s, 5c, 2d
    // A keeps: As, Qd (A-A-K-Q-8)
    // B keeps: Ad, Jh (A-A-K-J-8)
    u64 board5 = hand_mask({"Ah", "Kh", "8s", "5c", "2d"});
    u64 hand5_A = board5 | hand_mask({"As", "Qd"});
    u64 hand5_B = board5 | hand_mask({"Ad", "Jh"});

    std::uint32_t score5_A = eval7(hand5_A);
    std::uint32_t score5_B = eval7(hand5_B);

    if (score5_A > score5_B) {
        std::cout << "  [PASS] Ex. 5: Pair A-A-K-Q-8 (" << score5_A << ") beats A-A-K-J-8 (" << score5_B << ")" << std::endl;
    } else {
        std::cerr << "  [FAIL] Ex. 5: Kicker evaluation failed!" << std::endl;
    }
}