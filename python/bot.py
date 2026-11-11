import sys
import json
import math

RANKS = "23456789TJQKA"
SUIT_MAP = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
RANK_MAP = {r: i for i, r in enumerate(RANKS)}

def legalize_action(req, action, amount=None):
    """Sanitizes any proposed bot action to ensure it's 100% legal."""
    legal = req.get("legal_actions", ["check", "fold"])
    
    if action not in legal:
        if "check" in legal:
            return {"type": "action", "action": "check"}
        if "call" in legal:
            return {"type": "action", "action": "call"}
        return {"type": "action", "action": "fold"}

    if action == "raise":
        min_r = req.get("min_raise", 2)
        max_r = req.get("max_raise", 200)
        amount = min_r if amount is None else max(min_r, min(max_r, int(amount)))
        return {"type": "action", "action": "raise", "amount": amount}

    return {"type": "action", "action": action}

def choose_action(req):
    time_left = req.get("time_left_ms", 60000)
    
    # Emergency fast-mode if under 15 seconds remaining
    if time_left < 15000:
        if "check" in req.get("legal_actions", []):
            return {"type": "action", "action": "check"}
        return {"type": "action", "action": "call"} if "call" in req.get("legal_actions", []) else {"type": "action", "action": "fold"}
        
    if "check" in req.get("legal_actions", []):
        return legalize_action(req, "check")
    return legalize_action(req, "call")

def choose_discard(req):
    cards = req.get("hole_cards", [])
    if not cards:
        return {"type": "discard", "card": "2s"}
    worst = min(cards, key=lambda c: RANK_MAP.get(c[0], 0))
    return {"type": "discard", "card": worst}

def parse_card(c_str):
    return RANK_MAP[c_str[0]], SUIT_MAP[c_str[1]]

def eval5(cards5):
    """Evaluates a 5-card hand tuple ((r1, s1), ..., (r5, s5)) into a numerical score."""
    ranks = sorted([c[0] for c in cards5], reverse=True)
    suits = [c[1] for c in cards5]
    
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    is_straight = False
    straight_high = -1
    unique_ranks = sorted(list(set(ranks)), reverse=True)
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]
        elif unique_ranks == [12, 3, 2, 1, 0]: # A-2-3-4-5 wheel straight
            is_straight = True
            straight_high = 3

    # Group rank frequencies
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    
    # Sort by count frequency, then rank value
    freq_sorted = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    pattern = tuple(count for rank, count in freq_sorted)
    ordered_ranks = [rank for rank, count in freq_sorted]

    # Hand category scoring
    if is_flush and is_straight:
        category = 8
        kickers = [straight_high]
    elif pattern == (4, 1):
        category = 7
        kickers = ordered_ranks
    elif pattern == (3, 2):
        category = 6
        kickers = ordered_ranks
    elif is_flush:
        category = 5
        kickers = ranks
    elif is_straight:
        category = 4
        kickers = [straight_high]
    elif pattern == (3, 1, 1):
        category = 3
        kickers = ordered_ranks
    elif pattern == (2, 2, 1):
        category = 2
        kickers = ordered_ranks
    elif pattern == (2, 1, 1, 1):
        category = 1
        kickers = ordered_ranks
    else:
        category = 0
        kickers = ranks

    return (category, kickers)

def eval7_python(card_strings):
    """Standalone 7-card evaluator (best 5 out of 7 combinations)."""
    if len(card_strings) < 5:
        return (0, [])
    
    parsed = [parse_card(c) for c in card_strings]
    best_score = (-1, [])
    
    # Evaluate all 5-card combinations out of 7
    n = len(parsed)
    for i in range(n - 4):
        for j in range(i + 1, n - 3):
            for k in range(j + 1, n - 2):
                for l in range(k + 1, n - 1):
                    for m in range(l + 1, n):
                        hand = (parsed[i], parsed[j], parsed[k], parsed[l], parsed[m])
                        score = eval5(hand)
                        if score > best_score:
                            best_score = score
                            
    return best_score

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception as e:
            print(f"Error parsing line: {e}", file=sys.stderr)
            continue
        
        t = msg.get("type")
        reply = None
        
        try:
            if t == "action_request":
                reply = choose_action(msg)
            elif t == "discard_request":
                reply = choose_discard(msg)
            elif t == "match_end":
                break
        except Exception as err:
            print(f"Exception in bot handler: {err}", file=sys.stderr)
            if t == "action_request":
                reply = legalize_action(msg, "fold")
            elif t == "discard_request":
                cards = msg.get("hole_cards", ["2s"])
                card_to_discard = cards[0] if cards else "2s"
                reply = {"type": "discard", "card": card_to_discard}

        if reply:
            print(json.dumps(reply), flush=True)

if __name__ == "__main__":
    main()