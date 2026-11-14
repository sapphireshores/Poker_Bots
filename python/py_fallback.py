import base64
import itertools
import random
import struct
import zlib

_PREFLOP_B64 = "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"
_PREFLOP_LUT = None
_SUIT_PERMS = list(itertools.permutations(range(4)))

# Precompute straight detection table for all 8192 13-bit rank masks (O(1) lookup!)
_STRAIGHT_HI = [-1] * 8192
for _m in range(8192):
    if (_m & 0x100F) == 0x100F:
        _STRAIGHT_HI[_m] = 3
    for _hi in range(4, 13):
        if ((_m >> (_hi - 4)) & 0x1F) == 0x1F:
            _STRAIGHT_HI[_m] = _hi

# Precompute top-5 bits value for all 8192 13-bit rank masks (O(1) lookup!)
_TOP5_VAL = [0] * 8192
for _m in range(8192):
    _v = 0
    _cnt = 0
    for _r in range(12, -1, -1):
        if (_m >> _r) & 1:
            _v = (_v << 4) | _r
            _cnt += 1
            if _cnt == 5:
                break
    _TOP5_VAL[_m] = _v


def _canon_triple(c0, c1, c2):
    best = (99, 99, 99)
    r0, s0 = c0 % 13, c0 // 13
    r1, s1 = c1 % 13, c1 // 13
    r2, s2 = c2 % 13, c2 // 13
    for p in _SUIT_PERMS:
        t0 = p[s0] * 13 + r0
        t1 = p[s1] * 13 + r1
        t2 = p[s2] * 13 + r2
        if t0 > t1: t0, t1 = t1, t0
        if t1 > t2: t1, t2 = t2, t1
        if t0 > t1: t0, t1 = t1, t0
        cand = (t0, t1, t2)
        if cand < best:
            best = cand
    return best


def _ensure_preflop_lut():
    global _PREFLOP_LUT
    if _PREFLOP_LUT is not None:
        return
    raw = zlib.decompress(base64.b64decode(_PREFLOP_B64))
    vals = struct.unpack("<1755f", raw)
    lut = {}
    idx = 0
    for c0 in range(50):
        for c1 in range(c0 + 1, 51):
            for c2 in range(c1 + 1, 52):
                cn = _canon_triple(c0, c1, c2)
                if cn == (c0, c1, c2):
                    lut[cn] = vals[idx]
                    idx += 1
                else:
                    lut[(c0, c1, c2)] = lut[cn]
    _PREFLOP_LUT = lut


def lookup_preflop_3card(hole_ids):
    _ensure_preflop_lut()
    s = tuple(sorted(hole_ids[:3]))
    return float(_PREFLOP_LUT.get(s, 0.5))


def _eval7_fast(c0, c1, c2, c3, c4, c5, c6):
    """Direct O(1) bitmask 7-card evaluator (no 21-combination loop, no sorting)."""
    s0 = s1 = s2 = s3 = 0
    for c in (c0, c1, c2, c3, c4, c5, c6):
        bit = 1 << (c % 13)
        st = c // 13
        if st == 0: s0 |= bit
        elif st == 1: s1 |= bit
        elif st == 2: s2 |= bit
        else: s3 |= bit

    all_r = s0 | s1 | s2 | s3

    # Flush / Straight-flush check
    flush_mask = 0
    if s0.bit_count() >= 5: flush_mask = s0
    elif s1.bit_count() >= 5: flush_mask = s1
    elif s2.bit_count() >= 5: flush_mask = s2
    elif s3.bit_count() >= 5: flush_mask = s3

    if flush_mask:
        sf = _STRAIGHT_HI[flush_mask]
        if sf >= 0:
            return (8 << 20) | sf

    # Multiplicity bitboards across the 4 suits
    pairs = (s0 & s1) | (s0 & s2) | (s0 & s3) | (s1 & s2) | (s1 & s3) | (s2 & s3)
    trips = (s0 & s1 & s2) | (s0 & s1 & s3) | (s0 & s2 & s3) | (s1 & s2 & s3)
    quads = s0 & s1 & s2 & s3

    if quads:
        qr = quads.bit_length() - 1
        kicker = (all_r ^ quads).bit_length() - 1
        return (7 << 20) | (qr << 4) | kicker

    if trips:
        tr = trips.bit_length() - 1
        rem_pairs = pairs ^ (1 << tr)
        if rem_pairs:
            pr = rem_pairs.bit_length() - 1
            return (6 << 20) | (tr << 4) | pr

    if flush_mask:
        return (5 << 20) | _TOP5_VAL[flush_mask]

    st_hi = _STRAIGHT_HI[all_r]
    if st_hi >= 0:
        return (4 << 20) | st_hi

    if trips:
        tr = trips.bit_length() - 1
        singles = all_r ^ trips
        k1 = singles.bit_length() - 1
        k2 = (singles ^ (1 << k1)).bit_length() - 1
        return (3 << 20) | (tr << 8) | (k1 << 4) | k2

    if pairs:
        p1 = pairs.bit_length() - 1
        rem_p = pairs ^ (1 << p1)
        if rem_p:
            p2 = rem_p.bit_length() - 1
            kicker = (all_r ^ (1 << p1) ^ (1 << p2)).bit_length() - 1
            return (2 << 20) | (p1 << 8) | (p2 << 4) | kicker
        singles = all_r ^ (1 << p1)
        k1 = singles.bit_length() - 1
        s2_m = singles ^ (1 << k1)
        k2 = s2_m.bit_length() - 1
        k3 = (s2_m ^ (1 << k2)).bit_length() - 1
        return (1 << 20) | (p1 << 12) | (k1 << 8) | (k2 << 4) | k3

    return _TOP5_VAL[all_r]


def py_choose_discard(hole_ids, board_ids, dead_mask, n_samples=64):
    b0, b1, b2 = board_ids[0], board_ids[1], board_ids[2]
    best_d, best_val = 0, -1
    for d in range(3):
        a = hole_ids[1 if d == 0 else 0]
        b = hole_ids[2 if d == 2 else 1]
        # Score 5-card flop hand using _eval7_fast with 2 dummy distinct high-card impossible ranks via 5-card check
        s0 = s1 = s2 = s3 = 0
        for c in (b0, b1, b2, a, b):
            bit = 1 << (c % 13)
            st = c // 13
            if st == 0: s0 |= bit
            elif st == 1: s1 |= bit
            elif st == 2: s2 |= bit
            else: s3 |= bit
        all_r = s0 | s1 | s2 | s3
        pairs = (s0 & s1) | (s0 & s2) | (s0 & s3) | (s1 & s2) | (s1 & s3) | (s2 & s3)
        trips = (s0 & s1 & s2) | (s0 & s1 & s3) | (s0 & s2 & s3) | (s1 & s2 & s3)
        quads = s0 & s1 & s2 & s3
        is_fl = (s0 == all_r or s1 == all_r or s2 == all_r or s3 == all_r)
        st_hi = _STRAIGHT_HI[all_r]
        if is_fl and st_hi >= 0: s5 = (8 << 20) | st_hi
        elif quads: s5 = (7 << 20) | ((quads.bit_length() - 1) << 4)
        elif trips and (pairs ^ trips): s5 = (6 << 20) | ((trips.bit_length() - 1) << 4)
        elif is_fl: s5 = (5 << 20) | _TOP5_VAL[all_r]
        elif st_hi >= 0: s5 = (4 << 20) | st_hi
        elif trips: s5 = (3 << 20) | ((trips.bit_length() - 1) << 8)
        elif pairs:
            p1 = pairs.bit_length() - 1
            rem = pairs ^ (1 << p1)
            s5 = ((2 << 20) | (p1 << 8) | ((rem.bit_length() - 1) << 4)) if rem else ((1 << 20) | (p1 << 12))
        else:
            s5 = _TOP5_VAL[all_r]

        ra, sa = a % 13, a // 13
        rb, sb = b % 13, b // 13
        hi, lo = max(ra, rb), min(ra, rb)
        two_s = hi * 20 + lo * 10 + (200 + ra * 15 if ra == rb else 0) + (28 if sa == sb else 0)
        for sm in (s0, s1, s2, s3):
            if sm.bit_count() == 4:
                two_s += 42
        rmask = ((all_r << 1) | 1) if (all_r & (1 << 12)) else (all_r << 1)
        if any(((rmask >> lo_r) & 0x1F).bit_count() == 4 for lo_r in range(10)):
            two_s += 32
        val = (s5 << 12) + two_s
        if val > best_val:
            best_val, best_d = val, d
    return best_d


def py_choose_action(
    street_id, pot, to_call, my_bet, opp_bet, min_raise, max_raise, legal,
    hole_ids, board_ids, dead_mask, opp_fold_pre, opp_fold_post, opp_agg,
    is_button, cumulative_net, score_cap, n_samples=160
):
    cap_protect = 0.0
    if score_cap > 0:
        if cumulative_net >= score_cap + 60:
            cap_protect = 0.035
        elif cumulative_net <= -(score_cap + 60):
            cap_protect = -0.035

    pot = max(2.0, float(pot))
    to_call = float(to_call)
    bet_frac = to_call / max(2.0, pot - to_call)

    if street_id == 0 and len(hole_ids) >= 3:
        equity = lookup_preflop_3card(hole_ids)
        if opp_agg <= 0.45 and to_call > 0:
            if bet_frac >= 0.75: equity -= 0.035
            elif bet_frac >= 0.35: equity -= 0.020
        equity = max(0.05, min(0.95, equity))
    else:
        used = set(hole_ids) | set(board_ids)
        for c in range(52):
            if (dead_mask >> c) & 1:
                used.add(c)
        avail = [c for c in range(52) if c not in used]
        needed = max(0, 5 - len(board_ids))
        cands = (
            [(hole_ids[1], hole_ids[2]), (hole_ids[0], hole_ids[2]), (hole_ids[0], hole_ids[1])]
            if len(hole_ids) == 3 else [(hole_ids[0], hole_ids[1])]
        )
        eff_samples = 220 if pot >= 36 else (90 if pot <= 12 and to_call == 0 else max(140, n_samples))
        rng = random.Random()
        sample_fn = rng.sample
        eval7 = _eval7_fast
        eq_sums = [0.0] * len(cands)
        nb = len(board_ids)

        if nb == 3:
            b0, b1, b2 = board_ids[0], board_ids[1], board_ids[2]
            for _ in range(eff_samples):
                o0, o1, r3, r4 = sample_fn(avail, 4)
                opp_sc = eval7(b0, b1, b2, r3, r4, o0, o1)
                for idx, (m0, m1) in enumerate(cands):
                    my_sc = eval7(b0, b1, b2, r3, r4, m0, m1)
                    if my_sc > opp_sc: eq_sums[idx] += 1.0
                    elif my_sc == opp_sc: eq_sums[idx] += 0.5
        elif nb == 4:
            b0, b1, b2, b3 = board_ids[0], board_ids[1], board_ids[2], board_ids[3]
            for _ in range(eff_samples):
                o0, o1, r4 = sample_fn(avail, 3)
                opp_sc = eval7(b0, b1, b2, b3, r4, o0, o1)
                for idx, (m0, m1) in enumerate(cands):
                    my_sc = eval7(b0, b1, b2, b3, r4, m0, m1)
                    if my_sc > opp_sc: eq_sums[idx] += 1.0
                    elif my_sc == opp_sc: eq_sums[idx] += 0.5
        elif nb == 5:
            b0, b1, b2, b3, b4 = board_ids[0], board_ids[1], board_ids[2], board_ids[3], board_ids[4]
            for _ in range(eff_samples):
                o0, o1 = sample_fn(avail, 2)
                opp_sc = eval7(b0, b1, b2, b3, b4, o0, o1)
                for idx, (m0, m1) in enumerate(cands):
                    my_sc = eval7(b0, b1, b2, b3, b4, m0, m1)
                    if my_sc > opp_sc: eq_sums[idx] += 1.0
                    elif my_sc == opp_sc: eq_sums[idx] += 0.5
        else:
            for _ in range(eff_samples):
                d = sample_fn(avail, 7)
                opp_sc = eval7(d[2], d[3], d[4], d[5], d[6], d[0], d[1])
                for idx, (m0, m1) in enumerate(cands):
                    my_sc = eval7(d[2], d[3], d[4], d[5], d[6], m0, m1)
                    if my_sc > opp_sc: eq_sums[idx] += 1.0
                    elif my_sc == opp_sc: eq_sums[idx] += 0.5

        equity = max(eq_sums) / max(1, eff_samples)

    opp_fold = opp_fold_pre if street_id == 0 else opp_fold_post
    can_raise = ("raise" in legal and min_raise <= max_raise and max_raise > 0)

    if to_call > 0:
        if street_id == 0 and is_button == 1 and my_bet <= 1 and opp_bet == 2:
            if can_raise and equity >= 0.435 + cap_protect:
                return ("raise", max(min_raise, min(max_raise, 6)))
            if equity >= 0.30 + cap_protect:
                return ("call" if "call" in legal else "check", 0)
            return ("fold", 0)

        if can_raise and equity >= 0.64 + cap_protect:
            target = int(opp_bet + (pot + to_call) * (0.95 if equity >= 0.78 else 0.65))
            return ("raise", max(min_raise, min(max_raise, target)))

        call_ev = equity * (pot + to_call) - to_call
        risk_buf = pot * (0.04 + 0.07 * min(1.5, bet_frac) + cap_protect)
        if call_ev >= risk_buf:
            return ("call" if "call" in legal else "check", 0)
        return ("fold" if "fold" in legal else ("check" if "check" in legal else "call"), 0)

    if can_raise and equity >= 0.58 + cap_protect:
        target = int(opp_bet + pot * (0.80 if equity >= 0.75 else 0.52))
        return ("raise", max(min_raise, min(max_raise, target)))
    if can_raise and opp_fold > 0.55 and cap_protect <= 0.0 and equity >= 0.44 and random.random() < 0.45:
        target = int(opp_bet + pot * 0.35)
        return ("raise", max(min_raise, min(max_raise, target)))
    return ("check" if "check" in legal else "call", 0)
