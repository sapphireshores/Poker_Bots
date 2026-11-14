import ctypes
import gc
import json
import os
import sys
import time
import py_fallback

SUIT_MAP = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
RANK_MAP = {
    '2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
    '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12
}
STREET_MAP = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(BASE_DIR, "libpoker_solver.so")
BIN_PATH = os.path.join(BASE_DIR, "tables.bin").encode("utf-8")

ACTION_BUDGET_MS = 8.0
DISCARD_BUDGET_MS = 10.0

c_lib = None
if os.path.exists(LIB_PATH):
    try:
        _lib = ctypes.CDLL(LIB_PATH)
        _lib.py_init_engine.argtypes = [ctypes.c_char_p]
        _lib.py_init_engine.restype = None

        _lib.py_choose_discard.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint64,
            ctypes.c_double
        ]
        _lib.py_choose_discard.restype = ctypes.c_int

        _lib.py_choose_action.argtypes = [
            ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8,
            ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
            ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
            ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_int,
            ctypes.c_double,
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        ]
        _lib.py_choose_action.restype = None
        _lib.py_init_engine(BIN_PATH)
        c_lib = _lib
    except Exception as _load_err:
        sys.stderr.write(f"WARN: Could not load C++ solver ({_load_err}); using Python fallback.\n")
        sys.stderr.flush()
        c_lib = None


def _pair_strength(c1, c2):
    r1, s1 = RANK_MAP[c1[0]], SUIT_MAP[c1[1]]
    r2, s2 = RANK_MAP[c2[0]], SUIT_MAP[c2[1]]
    hi, lo = max(r1, r2), min(r1, r2)
    score = hi * 20 + lo * 10
    if r1 == r2:
        score += 200 + r1 * 15
    if s1 == s2:
        score += 28
    if hi - lo == 1:
        score += 18
    elif hi - lo == 2:
        score += 10
    return score


def _compute_dynamic_budget_ms(time_left_ms, hands_played, total_hands, pot, street, is_discard=False):
    hands_rem = max(1, total_hands - hands_played)
    usable_ms = max(400.0, time_left_ms * 0.65)
    per_hand_ms = usable_ms / hands_rem
    base = per_hand_ms * (0.18 if is_discard else 0.26)
    if pot >= 60:
        base *= 1.45
    elif pot >= 24:
        base *= 1.20
    if street in ("turn", "river"):
        base *= 1.15
    lo, hi = (2.0, 6.0) if is_discard else (2.4, 9.5)
    return max(lo, min(hi, base))


class OpponentTracker:
    def __init__(self):
        self.hands = 0
        self.vpip_hands = 0
        self.opp_actions = 0.0
        self.opp_raises = 0.0
        self.faced_bets_pre = 0.0
        self.folded_to_bets_pre = 0.0
        self.faced_bets_post = 0.0
        self.folded_to_bets_post = 0.0
        self.sd_count = 0
        self.sd_weak_sum = 0.0
        self.net_chips = 0

    def update_from_result(self, msg):
        history = msg.get("history", [])
        if history:
            self.hands += 1
            opp_put_money = False
            my_last_bet_street = None
            opp_first_preflop_acted = False
            for entry in history:
                if isinstance(entry, dict):
                    actor = entry.get("player", entry.get("actor", ""))
                    act = entry.get("action", "")
                    street = entry.get("street")
                elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    actor, act = entry[0], entry[1]
                    street = entry[2] if len(entry) >= 3 else None
                else:
                    continue

                is_opp = (actor in ("opp", 1, "B"))
                if is_opp:
                    self.opp_actions += 1.0
                    is_pre = (street in (None, "preflop") and not opp_first_preflop_acted) or (street == "preflop")
                    if is_pre:
                        if act in ("call", "raise", "bet"):
                            opp_put_money = True
                        if not opp_first_preflop_acted:
                            opp_first_preflop_acted = True
                            if my_last_bet_street is None:
                                self.faced_bets_pre += 1.0
                                if act == "fold":
                                    self.folded_to_bets_pre += 1.0
                    if act in ("raise", "bet"):
                        self.opp_raises += 1.0
                    if my_last_bet_street is not None:
                        if my_last_bet_street == "preflop":
                            self.faced_bets_pre += 1.0
                            if act == "fold":
                                self.folded_to_bets_pre += 1.0
                        else:
                            self.faced_bets_post += 1.0
                            if act == "fold":
                                self.folded_to_bets_post += 1.0
                    my_last_bet_street = None
                else:
                    if act in ("raise", "bet"):
                        my_last_bet_street = street if street is not None else "postflop"
                    elif act in ("call", "check", "fold"):
                        my_last_bet_street = None

            if opp_put_money:
                self.vpip_hands += 1

        delta = msg.get("net", msg.get("delta", msg.get("my_delta", msg.get("payoff", 0))))
        if isinstance(delta, (int, float)):
            self.net_chips += int(delta)

        opp_cards = msg.get("opp_hole_cards")
        if isinstance(opp_cards, list) and len(opp_cards) >= 2:
            strength = _pair_strength(opp_cards[0], opp_cards[1])
            looseness = max(-1.0, min(1.0, (235.0 - strength) / 120.0))
            self.sd_count += 1
            self.sd_weak_sum += looseness

    def get_stats(self):
        vpip = (self.vpip_hands + 4.0) / (self.hands + 8.0)
        agg = (self.opp_raises + 3.0) / (self.opp_actions + 12.0)
        fold_pre = (self.folded_to_bets_pre + 2.0) / (self.faced_bets_pre + 6.0)
        fold_post = (self.folded_to_bets_post + 3.0) / (self.faced_bets_post + 8.0)
        sd_loose = self.sd_weak_sum / (self.sd_count + 4.0)
        return (
            max(0.10, min(0.95, vpip)),
            max(0.05, min(0.85, agg)),
            max(0.10, min(0.90, fold_pre)),
            max(0.10, min(0.90, fold_post)),
            max(-1.0, min(1.0, sd_loose)),
        )


class LiveState:
    __slots__ = ['hole', 'board', 'flop_board', 'dead', 'opp_discard', 'is_button', 'opp_raised']

    def __init__(self):
        self.hole = []
        self.board = 0
        self.flop_board = 0
        self.dead = 0
        self.opp_discard = 0
        self.is_button = 0
        self.opp_raised = 0


def parse_card_id(card_str):
    return SUIT_MAP[card_str[1]] * 13 + RANK_MAP[card_str[0]]


def legalize_action(req, action_type, amount=0):
    legal = req.get("legal_actions", [])
    if action_type == "raise" and "raise" in legal:
        min_r = int(req.get("min_raise", 0))
        max_r = int(req.get("max_raise", 0))
        if min_r <= max_r and max_r > 0:
            clamped = max(min_r, min(max_r, int(amount)))
            return {"type": "action", "action": "raise", "amount": clamped}
        action_type = "call" if "call" in legal else "check"

    if action_type in legal:
        return {"type": "action", "action": action_type}

    if "check" in legal:
        return {"type": "action", "action": "check"}
    if "call" in legal:
        return {"type": "action", "action": "call"}
    if "fold" in legal:
        return {"type": "action", "action": "fold"}
    if legal:
        if legal[0] == "raise":
            return {"type": "action", "action": "raise", "amount": int(req.get("min_raise", 0))}
        return {"type": "action", "action": legal[0]}
    return {"type": "action", "action": "check"}


def choose_discard(req, state, time_left_ms, hands_played=0, total_hands=400):
    cards = req.get("hole_cards", state.hole)
    if not cards:
        return {"type": "discard", "card": "2s"}
    board_cards = req.get("board", [])

    if c_lib is not None and len(board_cards) >= 3 and len(cards) >= 3 and time_left_ms > 2000:
        hole_arr = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in cards[:3]])
        board_arr = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in board_cards[:3]])
        budget = _compute_dynamic_budget_ms(
            time_left_ms, hands_played, total_hands, int(req.get("pot", 6)), "flop", is_discard=True
        )
        drop_idx = int(c_lib.py_choose_discard(hole_arr, board_arr, state.dead, budget))
        if 0 <= drop_idx < len(cards):
            return {"type": "discard", "card": cards[drop_idx]}

    if len(board_cards) >= 3 and len(cards) >= 3 and time_left_ms > 2500:
        h_ids = [parse_card_id(c) for c in cards[:3]]
        b_ids = [parse_card_id(c) for c in board_cards[:3]]
        drop_idx = py_fallback.py_choose_discard(h_ids, b_ids, state.dead, n_samples=140)
        if 0 <= drop_idx < len(cards):
            return {"type": "discard", "card": cards[drop_idx]}

    worst_idx = min(range(len(cards)), key=lambda i: RANK_MAP.get(cards[i][0], 0))
    return {"type": "discard", "card": cards[worst_idx]}


def choose_action(req, state, tracker, time_left_ms, score_cap, total_hands=400):
    legal = req.get("legal_actions", [])

    if c_lib is None and state.hole and time_left_ms >= 600:
        street_name = req.get("street", "preflop")
        street_id = STREET_MAP.get(street_name, 0)
        pot = int(req.get("pot", 2))
        my_bet = int(req.get("my_bet", 0))
        opp_bet = int(req.get("opp_bet", 0))
        to_call = int(req.get("to_call", max(0, opp_bet - my_bet)))
        min_raise = int(req.get("min_raise", 0))
        max_raise = int(req.get("max_raise", 0))
        _, opp_agg, opp_fold_pre, opp_fold_post, _ = tracker.get_stats()
        h_ids = [parse_card_id(c) for c in state.hole[:3]]
        b_ids = [parse_card_id(c) for c in req.get("board", [])]
        n_samp = 0 if street_id == 0 else (28 if time_left_ms < 4000 else 72)
        act, amt = py_fallback.py_choose_action(
            street_id, pot, to_call, my_bet, opp_bet, min_raise, max_raise, legal,
            h_ids, b_ids, state.dead, opp_fold_pre, opp_fold_post, opp_agg,
            state.is_button, tracker.net_chips, score_cap, n_samples=n_samp
        )
        return legalize_action(req, act, amt)

    if c_lib is None or not state.hole or time_left_ms < 300:
        if "check" in legal:
            return legalize_action(req, "check")
        pot = max(1, int(req.get("pot", 2)))
        small = int(req.get("to_call", 0)) <= 0.33 * pot
        return legalize_action(req, "call" if small else "fold")

    low_time = time_left_ms < 2000

    hole_cards = state.hole
    hole_ids = (ctypes.c_uint8 * 3)(
        *[parse_card_id(c) for c in hole_cards[:3]] + [0] * (3 - len(hole_cards[:3]))
    )

    street_name = req.get("street", "preflop")
    street_id = STREET_MAP.get(street_name, 0)
    pot = int(req.get("pot", 2))
    my_stack = int(req.get("my_stack", 200))
    opp_stack = int(req.get("opp_stack", 200))
    my_bet = int(req.get("my_bet", 0))
    opp_bet = int(req.get("opp_bet", 0))
    to_call = int(req.get("to_call", max(0, opp_bet - my_bet)))

    min_raise = int(req.get("min_raise", 0))
    last_raise = max(2, min_raise - opp_bet) if min_raise > opp_bet else max(2, to_call)
    raises_left = int(req.get("raises_left", 4 if "raise" in legal else 0))

    opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose = tracker.get_stats()
    eff_stack = min(my_stack, opp_stack + max(0, opp_bet - my_bet))

    budget = 0.3 if low_time else _compute_dynamic_budget_ms(
        time_left_ms, tracker.hands, total_hands, pot, street_name, is_discard=False
    )

    out_action = ctypes.c_int(0)
    out_amount = ctypes.c_int(0)

    c_lib.py_choose_action(
        street_id, 0, raises_left,
        pot, eff_stack, opp_stack, my_bet, opp_bet, last_raise,
        state.board, state.flop_board, state.dead, state.opp_discard,
        hole_ids, len(hole_cards),
        budget,
        opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose,
        state.is_button, state.opp_raised, tracker.net_chips, score_cap,
        ctypes.byref(out_action), ctypes.byref(out_amount)
    )

    act_code = out_action.value
    if act_code == 2:
        return legalize_action(req, "raise", out_amount.value)
    elif act_code == 1:
        return legalize_action(req, "call" if "call" in legal else "check")
    else:
        return legalize_action(req, "check" if "check" in legal else "fold")


def main():
    gc.disable()
    current_state = LiveState()
    tracker = OpponentTracker()
    time_bank_ms = 60000.0
    total_spent_ms = 0.0
    total_hands = 400
    score_cap = 400

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        t0 = time.perf_counter()
        msg = None
        try:
            msg = json.loads(line)
            t = msg.get("type")
            reply = None

            if t == "init":
                if "time_bank_ms" in msg:
                    time_bank_ms = float(msg["time_bank_ms"])
                total_hands = int(msg.get("total_hands", 1000 if time_bank_ms > 100000 else 400))
                score_cap = 1000 if (total_hands > 600 or time_bank_ms > 100000) else 400
            elif t == "new_hand":
                current_state.hole = list(msg.get("hole_cards", []))
                current_state.board = 0
                current_state.flop_board = 0
                current_state.dead = 0
                current_state.opp_discard = 0
                current_state.opp_raised = 0
                seat = msg.get("seat", msg.get("button"))
                if seat in ("button", "BTN", "SB", 0) and seat is not False:
                    current_state.is_button = 1
                elif seat in ("big_blind", "BB", 1) and seat is not True:
                    current_state.is_button = 0
                else:
                    current_state.is_button = 1 if (tracker.hands % 2 == 0) else 0
                if "time_bank_ms" in msg:
                    time_bank_ms = float(msg["time_bank_ms"])
                    if time_bank_ms > 100000 and total_hands <= 400:
                        total_hands = 1000
                        score_cap = 1000
            elif t == "action_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                board_cards = msg.get("board", [])
                current_state.board = 0
                for c in board_cards:
                    current_state.board |= (1 << parse_card_id(c))
                if len(board_cards) == 3 and current_state.flop_board == 0:
                    current_state.flop_board = current_state.board

                my_b = int(msg.get("my_bet", 0))
                opp_b = int(msg.get("opp_bet", 0))
                street = msg.get("street", "preflop")
                if street == "preflop":
                    if my_b == 1 and opp_b == 2:
                        current_state.is_button = 1
                    elif my_b == 2 and opp_b >= 2:
                        current_state.is_button = 0
                    if opp_b > 2:
                        current_state.opp_raised = 1
                else:
                    if opp_b > my_b:
                        current_state.opp_raised = 1

                reply = choose_action(
                    msg, current_state, tracker,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms)),
                    score_cap,
                    total_hands
                )
            elif t == "discard_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                board_cards = msg.get("board", [])
                current_state.board = 0
                for c in board_cards:
                    current_state.board |= (1 << parse_card_id(c))
                if len(board_cards) == 3 and current_state.flop_board == 0:
                    current_state.flop_board = current_state.board
                reply = choose_discard(
                    msg, current_state,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms)),
                    tracker.hands,
                    total_hands
                )
            elif t == "discard_result":
                my_discard = msg.get("my_discard")
                opp_discard = msg.get("opp_discard")
                if my_discard:
                    current_state.dead |= (1 << parse_card_id(my_discard))
                if opp_discard:
                    current_state.dead |= (1 << parse_card_id(opp_discard))
                    current_state.opp_discard = (1 << parse_card_id(opp_discard))
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                elif my_discard:
                    current_state.hole = [c for c in current_state.hole if c != my_discard]
            elif t == "hand_result":
                tracker.update_from_result(msg)
                if tracker.hands % 50 == 0:
                    gc.collect()
            elif t == "match_end":
                break

            if reply is not None:
                sys.stdout.write(json.dumps(reply) + '\n')
                sys.stdout.flush()
            total_spent_ms += (time.perf_counter() - t0) * 1000.0

        except Exception as e:
            sys.stderr.write(f"ERROR: {str(e)}\n")
            sys.stderr.flush()
            if isinstance(msg, dict):
                mt = msg.get("type")
                if mt == "discard_request":
                    hc = msg.get("hole_cards", current_state.hole)
                    fallback_card = min(hc, key=lambda c: RANK_MAP.get(c[0], 0)) if hc else "2s"
                    sys.stdout.write(json.dumps({"type": "discard", "card": fallback_card}) + '\n')
                    sys.stdout.flush()
                elif mt == "action_request":
                    legal = msg.get("legal_actions", [])
                    to_call = int(msg.get("to_call", 0))
                    pot = max(1, int(msg.get("pot", 2)))
                    if to_call <= 0 and "check" in legal:
                        fb = legalize_action(msg, "check")
                    elif "call" in legal and to_call <= pot * 0.35:
                        fb = legalize_action(msg, "call")
                    else:
                        fb = legalize_action(msg, "check" if "check" in legal else "fold")
                    sys.stdout.write(json.dumps(fb) + '\n')
                    sys.stdout.flush()
            elif '"discard_request"' in line:
                fallback_card = current_state.hole[0] if current_state.hole else "2s"
                sys.stdout.write(json.dumps({"type": "discard", "card": fallback_card}) + '\n')
                sys.stdout.flush()
            elif '"action_request"' in line:
                sys.stdout.write(json.dumps({"type": "action", "action": "fold"}) + '\n')
                sys.stdout.flush()
            total_spent_ms += (time.perf_counter() - t0) * 1000.0


if __name__ == "__main__":
    main()
