import ctypes
import gc
import json
import os
import sys
import time

SUIT_MAP = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
RANK_MAP = {
    '2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
    '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12
}
STREET_MAP = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(BASE_DIR, "libpoker_solver.so")
BIN_PATH = os.path.join(BASE_DIR, "tables.bin").encode("utf-8")

ACTION_BUDGET_MS = 7.5
DISCARD_BUDGET_MS = 12.0

c_lib = None
if os.path.exists(LIB_PATH):
    c_lib = ctypes.CDLL(LIB_PATH)
    c_lib.py_init_engine.argtypes = [ctypes.c_char_p]
    c_lib.py_init_engine.restype = None

    c_lib.py_choose_discard.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint64,
        ctypes.c_double
    ]
    c_lib.py_choose_discard.restype = ctypes.c_int

    c_lib.py_choose_action.argtypes = [
        ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8,
        ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
        ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
        ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    c_lib.py_choose_action.restype = None
    c_lib.py_init_engine(BIN_PATH)


class OpponentTracker:
    def __init__(self):
        self.hands = 0
        self.vpip_hands = 0
        self.opp_actions = 0.0
        self.opp_raises = 0.0
        self.faced_bets = 0.0
        self.folded_to_bets = 0.0

    def update_from_history(self, history):
        if not history:
            return
        self.hands += 1
        opp_put_money = False
        my_last_bet = False
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
                if act in ("call", "raise", "bet") and street in (None, "preflop"):
                    opp_put_money = True
                if act in ("raise", "bet"):
                    self.opp_raises += 1.0
                if my_last_bet:
                    self.faced_bets += 1.0
                    if act == "fold":
                        self.folded_to_bets += 1.0
                my_last_bet = False
            else:
                if act in ("raise", "bet"):
                    my_last_bet = True
                elif act in ("call", "check", "fold"):
                    my_last_bet = False

        if opp_put_money:
            self.vpip_hands += 1

    def get_stats(self):
        vpip = (self.vpip_hands + 4.0) / (self.hands + 8.0)
        agg = (self.opp_raises + 3.0) / (self.opp_actions + 12.0)
        fold = (self.folded_to_bets + 3.0) / (self.faced_bets + 8.0)
        return (
            max(0.10, min(0.95, vpip)),
            max(0.05, min(0.85, agg)),
            max(0.10, min(0.90, fold)),
        )


class LiveState:
    __slots__ = ['hole', 'board', 'dead', 'pot', 'opp_discard']

    def __init__(self):
        self.hole = []
        self.board = 0
        self.dead = 0
        self.pot = 0
        self.opp_discard = 0


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


def choose_discard(req, state, time_left_ms):
    cards = req.get("hole_cards", state.hole)
    if not cards:
        return {"type": "discard", "card": "2s"}
    board_cards = req.get("board", [])

    if c_lib is not None and len(board_cards) >= 3 and len(cards) >= 3 and time_left_ms > 2000:
        hole_arr = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in cards[:3]])
        board_arr = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in board_cards[:3]])
        drop_idx = int(c_lib.py_choose_discard(hole_arr, board_arr, state.dead, DISCARD_BUDGET_MS))
        if 0 <= drop_idx < len(cards):
            return {"type": "discard", "card": cards[drop_idx]}

    worst_idx = min(range(len(cards)), key=lambda i: RANK_MAP[cards[i][0]])
    return {"type": "discard", "card": cards[worst_idx]}


def choose_action(req, state, tracker, time_left_ms):
    legal = req.get("legal_actions", [])

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

    street_id = STREET_MAP.get(req.get("street", "preflop"), 0)
    pot = int(req.get("pot", 2))
    my_stack = int(req.get("my_stack", 200))
    opp_stack = int(req.get("opp_stack", 200))
    my_bet = int(req.get("my_bet", 0))
    opp_bet = int(req.get("opp_bet", 0))
    to_call = int(req.get("to_call", max(0, opp_bet - my_bet)))

    min_raise = int(req.get("min_raise", 0))
    last_raise = max(2, min_raise - opp_bet) if min_raise > opp_bet else max(2, to_call)
    raises_left = 4 if "raise" in legal else 0

    opp_vpip, opp_agg, opp_fold = tracker.get_stats()

    out_action = ctypes.c_int(0)
    out_amount = ctypes.c_int(0)

    c_lib.py_choose_action(
        street_id, 0, raises_left,
        pot, my_stack, opp_stack, my_bet, opp_bet, last_raise,
        state.board, state.dead, state.opp_discard,
        hole_ids, len(hole_cards),
        (0.3 if low_time else ACTION_BUDGET_MS),
        opp_vpip, opp_agg, opp_fold,
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

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        t0 = time.perf_counter()
        try:
            msg = json.loads(line)
            t = msg.get("type")
            reply = None

            if t == "new_hand":
                current_state.hole = list(msg.get("hole_cards", []))
                current_state.board = 0
                current_state.dead = 0
                current_state.pot = 3
                current_state.opp_discard = 0
                if "time_bank_ms" in msg:
                    time_bank_ms = float(msg["time_bank_ms"])
            elif t == "action_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                current_state.board = 0
                for c in msg.get("board", []):
                    current_state.board |= (1 << parse_card_id(c))
                reply = choose_action(
                    msg, current_state, tracker,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms))
                )
            elif t == "discard_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                current_state.board = 0
                for c in msg.get("board", []):
                    current_state.board |= (1 << parse_card_id(c))
                reply = choose_discard(
                    msg, current_state,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms))
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
                tracker.update_from_history(msg.get("history", []))
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
            if '"discard_request"' in line:
                fallback_card = current_state.hole[0] if current_state.hole else "2s"
                sys.stdout.write(json.dumps({"type": "discard", "card": fallback_card}) + '\n')
            else:
                sys.stdout.write(json.dumps({"type": "action", "action": "fold"}) + '\n')
            sys.stdout.flush()

if __name__ == "__main__":
    main()