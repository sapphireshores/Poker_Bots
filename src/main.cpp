#include "state.hpp"
#include "evaluator.hpp"
#include "abstraction.hpp"
#include "flatmap.hpp"
#include <chrono>
#include <string>
#include <stdexcept>

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

    u64 board = hand_mask({"Th", "9c", "2h", "3c", "4h"});
    u64 hand_A = board | hand_mask({"Qh", "Jh"});
    u64 hand_B = board | hand_mask({"9s", "9h"});

    std::uint32_t score_A = eval7(hand_A);
    std::uint32_t score_B = eval7(hand_B);

    if (score_A > score_B) {
        std::cout << "  [PASS] Ex. 1: Queen-high Flush (" << score_A << ") beats Trip 9s (" << score_B << ")" << std::endl;
    } else {
        std::cerr << "  [FAIL] Ex. 1: Evaluator returned incorrect winner! (A: " << score_A << ", B: " << score_B << ")" << std::endl;
    }

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

State create_initial_state() {
    State s = {};
    s.street = PRE;
    s.toAct = 0;
    s.stack[0] = 199;
    s.stack[1] = 198;
    s.bet[0] = 1;
    s.bet[1] = 2;
    s.pot = 0;
    s.raisesLeft = 3;
    s.acted[0] = false;
    s.acted[1] = false;
    return s;
}

void run_state_machine_tests() {
    std::cout << "[Validation] Running State Machine Phase 2.6 Tests..." << std::endl;
    
    State s2 = create_initial_state();
    apply_action(s2, CALL);
    apply_action(s2, RAISE, 6);
    apply_action(s2, CALL);
    
    if (s2.street == FLOP && s2.pot == 12 && s2.stack[0] == 194 && s2.stack[1] == 194) {
        std::cout << "  [PASS] Ex. 2: Chip conservation and Flop transition correct." << std::endl;
    } else {
        std::cerr << "  [FAIL] Ex. 2: State mismatch on Flop transition." << std::endl;
    }
    
    State s3 = create_initial_state();
    apply_action(s3, RAISE, 6);
    apply_action(s3, RAISE, 14);
    apply_action(s3, RAISE, 30);
    
    ActionContext ctx = get_action_context(s3);
    if (!ctx.can_raise && s3.raisesLeft == 0) {
        std::cout << "  [PASS] Ex. 3: 4-bet cap strictly enforced." << std::endl;
    } else {
        std::cerr << "  [FAIL] Ex. 3: Cap violation. Player can still raise." << std::endl;
    }
    
    State s4 = create_initial_state();
    apply_action(s4, FOLD);
    
    if (s4.street == SHOWDOWN) {
        std::cout << "  [PASS] Ex. 4: Fold instantly terminates the hand." << std::endl;
    } else {
        std::cerr << "  [FAIL] Ex. 4: Fold did not bypass remaining streets." << std::endl;
    }
}

int main() {
    std::cout << "Initializing 7-card evaluator tables. This will take a few seconds..." << std::endl;
    init_evaluator_tables();
    build_preflop_classes();
    run_validation_tests();
    run_state_machine_tests();
    export_tables_to_python("../python/tables.py");
    return 0;
}