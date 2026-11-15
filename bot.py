"""Discard Hold'em bot - single self-contained file """
import base64
import gc
import itertools
import json
import random
import struct
import sys
import time
import zlib

_PREFLOP_B64 = "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"
_PREFLOP_LUT = None
_SUIT_PERMS = list(itertools.permutations(range(4)))

# O(1) lookup tables for 13-bit rank masks
_STRAIGHT_HI = [-1] * 8192
_TOP5_VAL = [0] * 8192
for _m in range(8192):
    if (_m & 0x100F) == 0x100F:
        _STRAIGHT_HI[_m] = 3
    for _hi in range(4, 13):
        if ((_m >> (_hi - 4)) & 0x1F) == 0x1F:
            _STRAIGHT_HI[_m] = _hi
    _v = 0
    _cnt = 0
    for _r in range(12, -1, -1):
        if (_m >> _r) & 1:
            _v = (_v << 4) | _r
            _cnt += 1
            if _cnt == 5:
                break
    _TOP5_VAL[_m] = _v

# Precompute 2-card preflop strength for all 52x52 pairs
_PAIR_STR = [[0] * 52 for _ in range(52)]
for _a in range(52):
    _ra, _sa = _a % 13, _a // 13
    for _b in range(52):
        _rb, _sb = _b % 13, _b // 13
        _hi, _lo = (_ra, _rb) if _ra >= _rb else (_rb, _ra)
        _sc = _hi * 20 + _lo * 10
        if _ra == _rb:
            _sc += 200 + _ra * 15
        if _sa == _sb:
            _sc += 28
        if _hi - _lo == 1:
            _sc += 18
        elif _hi - _lo == 2:
            _sc += 10
        _PAIR_STR[_a][_b] = _sc


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


def _eval5_fast(c0, c1, c2, c3, c4):
    s0 = s1 = s2 = s3 = 0
    for c in (c0, c1, c2, c3, c4):
        bit = 1 << (c % 13)
        st = c // 13
        if st == 0: s0 |= bit
        elif st == 1: s1 |= bit
        elif st == 2: s2 |= bit
        else: s3 |= bit
    all_r = s0 | s1 | s2 | s3
    is_fl = (s0.bit_count() == 5 or s1.bit_count() == 5 or s2.bit_count() == 5 or s3.bit_count() == 5)
    st_hi = _STRAIGHT_HI[all_r]
    if is_fl and st_hi >= 0:
        return (8 << 20) | st_hi
    pairs = (s0 & s1) | (s0 & s2) | (s0 & s3) | (s1 & s2) | (s1 & s3) | (s2 & s3)
    trips = (s0 & s1 & s2) | (s0 & s1 & s3) | (s0 & s2 & s3) | (s1 & s2 & s3)
    quads = s0 & s1 & s2 & s3
    if quads:
        qr = quads.bit_length() - 1
        return (7 << 20) | (qr << 4) | ((all_r ^ quads).bit_length() - 1)
    if trips and (pairs ^ trips):
        tr = trips.bit_length() - 1
        return (6 << 20) | (tr << 4) | ((pairs ^ trips).bit_length() - 1)
    if is_fl:
        return (5 << 20) | _TOP5_VAL[all_r]
    if st_hi >= 0:
        return (4 << 20) | st_hi
    if trips:
        tr = trips.bit_length() - 1
        singles = all_r ^ trips
        k1 = singles.bit_length() - 1
        return (3 << 20) | (tr << 8) | (k1 << 4) | ((singles ^ (1 << k1)).bit_length() - 1)
    if pairs:
        p1 = pairs.bit_length() - 1
        rem = pairs ^ (1 << p1)
        if rem:
            p2 = rem.bit_length() - 1
            return (2 << 20) | (p1 << 8) | (p2 << 4) | ((all_r ^ (1 << p1) ^ (1 << p2)).bit_length() - 1)
        singles = all_r ^ (1 << p1)
        k1 = singles.bit_length() - 1
        s2_m = singles ^ (1 << k1)
        k2 = s2_m.bit_length() - 1
        return (1 << 20) | (p1 << 12) | (k1 << 8) | (k2 << 4) | ((s2_m ^ (1 << k2)).bit_length() - 1)
    return _TOP5_VAL[all_r]


def _eval7_fast(c0, c1, c2, c3, c4, c5, c6):
    s0 = s1 = s2 = s3 = 0
    for c in (c0, c1, c2, c3, c4, c5, c6):
        bit = 1 << (c % 13)
        st = c // 13
        if st == 0: s0 |= bit
        elif st == 1: s1 |= bit
        elif st == 2: s2 |= bit
        else: s3 |= bit

    all_r = s0 | s1 | s2 | s3

    flush_mask = 0
    if s0.bit_count() >= 5: flush_mask = s0
    elif s1.bit_count() >= 5: flush_mask = s1
    elif s2.bit_count() >= 5: flush_mask = s2
    elif s3.bit_count() >= 5: flush_mask = s3

    if flush_mask:
        sf = _STRAIGHT_HI[flush_mask]
        if sf >= 0:
            return (8 << 20) | sf

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


def _flop_keep_val(b0, b1, b2, a, b):
    s5 = _eval5_fast(b0, b1, b2, a, b)
    two_s = _PAIR_STR[a][b]
    sc = [0, 0, 0, 0]
    rmask = 0
    for c in (b0, b1, b2, a, b):
        sc[c // 13] += 1
        rmask |= (1 << (c % 13))
    if 4 in sc:
        two_s += 42
    rmask = ((rmask << 1) | 1) if (rmask & (1 << 12)) else (rmask << 1)
    for lo_r in range(10):
        if ((rmask >> lo_r) & 0x1F).bit_count() == 4:
            two_s += 32
            break
    return (s5 << 12) + two_s


def _pair_range_weight(a, b, opp_d, has_flop, fb0, fb1, fb2, min_opp_str, passive_cap):
    if opp_d >= 0:
        if has_flop:
            v12 = _flop_keep_val(fb0, fb1, fb2, a, b)
            if v12 < _flop_keep_val(fb0, fb1, fb2, a, opp_d) or v12 < _flop_keep_val(fb0, fb1, fb2, b, opp_d):
                return 0.0
        else:
            s12 = _PAIR_STR[a][b]
            if s12 < _PAIR_STR[a][opp_d] or s12 < _PAIR_STR[b][opp_d]:
                return 0.0
    s12 = _PAIR_STR[a][b]
    w = 1.0 if s12 >= min_opp_str else 0.02
    if passive_cap and s12 >= 600:
        w *= 0.30
    return w


def _exact_river_equity(board_ids, m0, m1, avail, opp_d, has_flop, fb0, fb1, fb2, min_opp_str, passive_cap):
    b0, b1, b2, b3, b4 = board_ids[0], board_ids[1], board_ids[2], board_ids[3], board_ids[4]
    bs = [0, 0, 0, 0]
    for bc in (b0, b1, b2, b3, b4):
        bs[bc // 13] |= 1 << (bc % 13)
    bs0, bs1, bs2, bs3 = bs[0], bs[1], bs[2], bs[3]
    straight_hi = _STRAIGHT_HI
    top5_val = _TOP5_VAL

    def eval_with_board(c5, c6):
        s0, s1, s2, s3 = bs0, bs1, bs2, bs3
        b5, st5 = 1 << (c5 % 13), c5 // 13
        if st5 == 0: s0 |= b5
        elif st5 == 1: s1 |= b5
        elif st5 == 2: s2 |= b5
        else: s3 |= b5
        b6, st6 = 1 << (c6 % 13), c6 // 13
        if st6 == 0: s0 |= b6
        elif st6 == 1: s1 |= b6
        elif st6 == 2: s2 |= b6
        else: s3 |= b6

        all_r = s0 | s1 | s2 | s3
        fl = s0 if s0.bit_count() >= 5 else (s1 if s1.bit_count() >= 5 else (s2 if s2.bit_count() >= 5 else (s3 if s3.bit_count() >= 5 else 0)))
        if fl:
            sf = straight_hi[fl]
            if sf >= 0:
                return (8 << 20) | sf
        pairs = (s0 & s1) | (s0 & s2) | (s0 & s3) | (s1 & s2) | (s1 & s3) | (s2 & s3)
        trips = (s0 & s1 & s2) | (s0 & s1 & s3) | (s0 & s2 & s3) | (s1 & s2 & s3)
        quads = s0 & s1 & s2 & s3
        if quads:
            qr = quads.bit_length() - 1
            return (7 << 20) | (qr << 4) | ((all_r ^ quads).bit_length() - 1)
        if trips:
            tr = trips.bit_length() - 1
            rem_p = pairs ^ (1 << tr)
            if rem_p:
                return (6 << 20) | (tr << 4) | (rem_p.bit_length() - 1)
        if fl:
            return (5 << 20) | top5_val[fl]
        st_h = straight_hi[all_r]
        if st_h >= 0:
            return (4 << 20) | st_h
        if trips:
            tr = trips.bit_length() - 1
            singles = all_r ^ trips
            k1 = singles.bit_length() - 1
            return (3 << 20) | (tr << 8) | (k1 << 4) | ((singles ^ (1 << k1)).bit_length() - 1)
        if pairs:
            p1 = pairs.bit_length() - 1
            rem_p = pairs ^ (1 << p1)
            if rem_p:
                p2 = rem_p.bit_length() - 1
                return (2 << 20) | (p1 << 8) | (p2 << 4) | ((all_r ^ (1 << p1) ^ (1 << p2)).bit_length() - 1)
            singles = all_r ^ (1 << p1)
            k1 = singles.bit_length() - 1
            s2_m = singles ^ (1 << k1)
            k2 = s2_m.bit_length() - 1
            return (1 << 20) | (p1 << 12) | (k1 << 8) | (k2 << 4) | ((s2_m ^ (1 << k2)).bit_length() - 1)
        return top5_val[all_r]

    my_sc = eval_with_board(m0, m1)
    acc = wsum = u_acc = 0.0
    u_cnt = 0
    nu = len(avail)
    for i in range(nu - 1):
        a = avail[i]
        for j in range(i + 1, nu):
            b = avail[j]
            opp_sc = eval_with_board(a, b)
            res = 1.0 if my_sc > opp_sc else (0.5 if my_sc == opp_sc else 0.0)
            u_acc += res
            u_cnt += 1
            w = _pair_range_weight(a, b, opp_d, has_flop, fb0, fb1, fb2, min_opp_str, passive_cap)
            if w > 0.0:
                acc += w * res
                wsum += w
    if wsum > 1e-12:
        return acc / wsum
    return (u_acc / u_cnt) if u_cnt > 0 else 0.5


def _exact_turn_equity(board_ids, m0, m1, avail, opp_d, has_flop, fb0, fb1, fb2, min_opp_str, passive_cap, t_end):
    b0, b1, b2, b3 = board_ids[0], board_ids[1], board_ids[2], board_ids[3]
    eval7 = _eval7_fast
    nu = len(avail)
    pair_w = [[0.0] * nu for _ in range(nu)]
    for i in range(nu - 1):
        a = avail[i]
        for j in range(i + 1, nu):
            b = avail[j]
            pair_w[i][j] = _pair_range_weight(a, b, opp_d, has_flop, fb0, fb1, fb2, min_opp_str, passive_cap)

    acc = wsum = u_acc = 0.0
    u_cnt = 0
    r_order = list(range(nu))
    random.shuffle(r_order)
    for step, r_idx in enumerate(r_order):
        if step >= 1 and time.perf_counter() >= t_end:
            break
        rc = avail[r_idx]
        my_sc = eval7(b0, b1, b2, b3, rc, m0, m1)
        for i in range(nu - 1):
            if i == r_idx:
                continue
            a = avail[i]
            pw_i = pair_w[i]
            for j in range(i + 1, nu):
                if j == r_idx:
                    continue
                opp_sc = eval7(b0, b1, b2, b3, rc, a, avail[j])
                res = 1.0 if my_sc > opp_sc else (0.5 if my_sc == opp_sc else 0.0)
                u_acc += res
                u_cnt += 1
                w = pw_i[j]
                if w > 0.0:
                    acc += w * res
                    wsum += w
    if wsum > 1e-12:
        return acc / wsum
    return (u_acc / u_cnt) if u_cnt > 0 else 0.5


def py_choose_discard(hole_ids, board_ids, dead_mask, budget_ms=3.5):
    t_end = time.perf_counter() + (budget_ms * 0.001)
    b0, b1, b2 = board_ids[0], board_ids[1], board_ids[2]
    h0, h1, h2 = hole_ids[0], hole_ids[1], hole_ids[2]

    used = {h0, h1, h2, b0, b1, b2}
    for c in range(52):
        if (dead_mask >> c) & 1:
            used.add(c)

    avail = [c for c in range(52) if c not in used]
    wins = [0.0, 0.0, 0.0]
    rng = random.Random()
    sample_fn = rng.sample
    eval7 = _eval7_fast
    keep_val = _flop_keep_val
    pairs = ((h1, h2), (h0, h2), (h0, h1))

    iters = 0
    while iters < 420:
        if (iters & 31) == 31 and time.perf_counter() >= t_end:
            break

        o0, o1, o2, r3, r4 = sample_fn(avail, 5)
        v01 = keep_val(b0, b1, b2, o0, o1)
        v02 = keep_val(b0, b1, b2, o0, o2)
        v12 = keep_val(b0, b1, b2, o1, o2)
        if v01 >= v02 and v01 >= v12:
            ko0, ko1 = o0, o1
        elif v02 >= v12:
            ko0, ko1 = o0, o2
        else:
            ko0, ko1 = o1, o2

        opp_sc = eval7(b0, b1, b2, r3, r4, ko0, ko1)
        for d in range(3):
            my_sc = eval7(b0, b1, b2, r3, r4, pairs[d][0], pairs[d][1])
            if my_sc > opp_sc:
                wins[d] += 1.0
            elif my_sc == opp_sc:
                wins[d] += 0.5
        iters += 1

    best_d = 0
    best_sc = -1.0
    for d in range(3):
        tie_b = 1e-4 * max(1, iters) * (_PAIR_STR[pairs[d][0]][pairs[d][1]] / 1000.0)
        if wins[d] + tie_b > best_sc:
            best_sc = wins[d] + tie_b
            best_d = d
    return best_d


def py_choose_action(
    street_id, pot, to_call, my_bet, opp_bet, min_raise, max_raise, legal,
    hole_ids, board_ids, flop_board_ids, dead_mask, opp_discard_id,
    opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose,
    is_button, opp_raised, cumulative_net, score_cap,
    budget_ms=4.5
):
    t_end = time.perf_counter() + (budget_ms * 0.001)

    cap_protect = 0.0
    if score_cap > 0:
        if cumulative_net >= score_cap + 60:
            cap_protect = 0.035
        elif cumulative_net <= -(score_cap + 60):
            cap_protect = -0.035

    pot = max(2.0, float(pot))
    to_call = float(to_call)
    bet_frac = to_call / max(2.0, pot - to_call)

    opp_fold = opp_fold_pre if street_id == 0 else opp_fold_post
    eff_vpip = max(0.10, min(0.95, opp_vpip + opp_sd_loose * 0.15))
    is_maniac = (opp_agg > 0.45)
    is_overfolder = (opp_fold > 0.55)
    is_station = (eff_vpip > 0.70 and opp_fold < 0.30)

    used = set(hole_ids) | set(board_ids)
    for c in range(52):
        if (dead_mask >> c) & 1:
            used.add(c)

    nb = len(board_ids)
    needed_board = max(0, 5 - nb)

    rng = random.Random()

    if nb == 0 and len(hole_ids) >= 3:
        equity = lookup_preflop_3card(hole_ids)
        if not is_maniac and to_call > 0.0:
            if bet_frac >= 0.75: equity -= 0.035
            elif bet_frac >= 0.35: equity -= 0.020
        equity = max(0.05, min(0.95, equity))
    else:
        avail = [c for c in range(52) if c not in used]
        cands = (
            [(hole_ids[1], hole_ids[2]), (hole_ids[0], hole_ids[2]), (hole_ids[0], hole_ids[1])]
            if len(hole_ids) == 3 else [(hole_ids[0], hole_ids[1])]
        )
        ncand = len(cands)

        min_opp_str = 0
        if not is_maniac and to_call > 0.0:
            sd_off = int(opp_sd_loose * 30.0)
            tight_bonus = 45 if (eff_vpip < 0.42 and opp_agg < 0.35) else 0
            if bet_frac >= 0.65: min_opp_str = max(0, 215 + tight_bonus - sd_off)
            elif bet_frac >= 0.35: min_opp_str = max(0, 170 + (tight_bonus // 2) - sd_off)
            else: min_opp_str = max(0, 130 - sd_off)

        passive_cap = (nb >= 4 and opp_raised == 0 and opp_agg >= 0.12)
        has_flop = (len(flop_board_ids) == 3)
        fb0 = flop_board_ids[0] if has_flop else 0
        fb1 = flop_board_ids[1] if has_flop else 0
        fb2 = flop_board_ids[2] if has_flop else 0

        # Exact River (C(43,2)=903 pairs, zero MC noise) & Exact Turn
        if ncand == 1 and nb == 5:
            equity = _exact_river_equity(
                board_ids, cands[0][0], cands[0][1], avail, opp_discard_id,
                has_flop, fb0, fb1, fb2, min_opp_str, passive_cap
            )
        elif ncand == 1 and nb == 4:
            equity = _exact_turn_equity(
                board_ids, cands[0][0], cands[0][1], avail, opp_discard_id,
                has_flop, fb0, fb1, fb2, min_opp_str, passive_cap, t_end
            )
        else:
            eq_sums = [0.0] * ncand
            max_iters = 560 if pot >= 36 else (300 if pot <= 12 and to_call == 0 else 420)
            sample_fn = rng.sample
            eval7 = _eval7_fast
            pair_str = _PAIR_STR
            iters = 0

            while iters < max_iters:
                if (iters & 31) == 31 and time.perf_counter() >= t_end:
                    break

                # Standard flop / preflop MC with range filtering
                o0 = o1 = r3 = r4 = 0
                d7 = None
                for att in range(10):
                    if nb == 3:
                        o0, o1, r3, r4 = sample_fn(avail, 4)
                    else:
                        d7 = sample_fn(avail, 7)
                        o0, o1 = d7[0], d7[1]

                    if att < 9:
                        if opp_discard_id >= 0:
                            if has_flop:
                                v12 = _flop_keep_val(fb0, fb1, fb2, o0, o1)
                                if v12 < _flop_keep_val(fb0, fb1, fb2, o0, opp_discard_id) or v12 < _flop_keep_val(fb0, fb1, fb2, o1, opp_discard_id):
                                    continue
                            else:
                                s12 = pair_str[o0][o1]
                                if s12 < pair_str[o0][opp_discard_id] or s12 < pair_str[o1][opp_discard_id]:
                                    continue
                        s12 = pair_str[o0][o1]
                        if s12 < min_opp_str:
                            continue
                    break

                if nb == 3:
                    b0, b1, b2 = board_ids[0], board_ids[1], board_ids[2]
                    opp_sc = eval7(b0, b1, b2, r3, r4, o0, o1)
                    for idx, (m0, m1) in enumerate(cands):
                        my_sc = eval7(b0, b1, b2, r3, r4, m0, m1)
                        if my_sc > opp_sc: eq_sums[idx] += 1.0
                        elif my_sc == opp_sc: eq_sums[idx] += 0.5
                else:
                    opp_sc = eval7(d7[2], d7[3], d7[4], d7[5], d7[6], o0, o1)
                    for idx, (m0, m1) in enumerate(cands):
                        my_sc = eval7(d7[2], d7[3], d7[4], d7[5], d7[6], m0, m1)
                        if my_sc > opp_sc: eq_sums[idx] += 1.0
                        elif my_sc == opp_sc: eq_sums[idx] += 0.5
                iters += 1

            equity = (max(eq_sums) / iters) if iters > 0 else 0.5

    if to_call > 0.0 and (nb == 3 or nb == 4):
        equity += 0.015 if is_button == 1 else -0.025
        equity = max(0.02, min(0.98, equity))

    jitter = (rng.random() - 0.5) * 0.22
    can_raise = ("raise" in legal and min_raise <= max_raise and max_raise > 0)

    # 1. Facing a bet / raise
    if to_call > 0.0:
        call_ev = equity * (pot + to_call) - to_call

        if nb == 0 and is_button == 1 and my_bet <= 1 and opp_bet == 2:
            open_thresh = (0.365 if is_overfolder else 0.435) + cap_protect
            if can_raise and equity >= open_thresh:
                return ("raise", max(min_raise, min(max_raise, 6)))
            if equity >= 0.30 + cap_protect:
                return ("call" if "call" in legal else "check", 0)
            return ("fold", 0)

        raise_thresh = (0.57 if is_station else 0.64) + cap_protect
        if nb == 0 and my_bet >= 4 and opp_agg > 0.35:
            raise_thresh -= 0.03
        if can_raise and equity >= raise_thresh:
            base_mult = 1.0 if equity >= 0.78 else 0.68
            if is_station:
                base_mult += 0.25
            mult = max(0.45, base_mult + jitter)
            target = int(opp_bet + (pot + to_call) * mult)
            raise_to = max(min_raise, min(max_raise, target))
            added_risk = float(raise_to - my_bet)
            fold_eq = 0.05 if is_station else opp_fold * 0.75
            eq_cont = max(0.05, equity - fold_eq * 0.22)
            final_pot_called = pot + added_risk + max(0.0, added_risk - to_call)
            raise_ev = fold_eq * pot + (1.0 - fold_eq) * (eq_cont * final_pot_called - added_risk)
            if raise_ev >= call_ev:
                return ("raise", raise_to)

        if can_raise and is_overfolder and not is_maniac and cap_protect <= 0.0 and 0.44 <= equity < 0.56 and rng.random() < 0.28:
            mult = max(0.40, 0.55 + jitter)
            target = int(opp_bet + (pot + to_call) * mult)
            raise_to = max(min_raise, min(max_raise, target))
            added_risk = float(raise_to - my_bet)
            fold_eq = opp_fold * 0.80
            eq_cont = max(0.05, equity - fold_eq * 0.22)
            final_pot_called = pot + added_risk + max(0.0, added_risk - to_call)
            bluff_ev = fold_eq * pot + (1.0 - fold_eq) * (eq_cont * final_pot_called - added_risk)
            if bluff_ev > 0.0:
                return ("raise", raise_to)

        risk_buffer = pot * (0.04 + 0.07 * min(1.5, bet_frac) + cap_protect)
        if is_maniac:
            risk_buffer -= pot * 0.06
            if equity >= 0.54:
                return ("call" if "call" in legal else "check", 0)
        if opp_agg < 0.12 and bet_frac > 0.8:
            risk_buffer += pot * 0.06
        if nb == 0 and bet_frac >= 0.75:
            if is_button == 0:
                risk_buffer += pot * 0.03
            elif my_bet >= 4 and eff_vpip < 0.45 and opp_agg < 0.25:
                risk_buffer += pot * 0.05

        if call_ev >= risk_buffer:
            return ("call" if "call" in legal else "check", 0)
        return ("fold" if "fold" in legal else ("check" if "check" in legal else "call"), 0)

    # 2. Free to check
    if can_raise:
        if nb == 4 and 0.54 <= equity < 0.62 and not is_station:
            return ("check" if "check" in legal else "call", 0)

        value_thresh = (0.50 if is_station else 0.58) + cap_protect
        if equity >= value_thresh:
            if nb == 5 and equity >= 0.86 and opp_fold < 0.65:
                base_frac = 1.22
            else:
                base_frac = 0.88 if equity >= 0.75 else 0.55
            if is_station:
                base_frac += 0.25
            frac = max(0.33, base_frac + jitter)
            target = int(opp_bet + pot * frac)
            bet_amt = max(min_raise, min(max_raise, target))
            if bet_amt >= min_raise:
                return ("raise", bet_amt)

        bluff_pct = 0.24
        if is_station or is_maniac or cap_protect > 0.0:
            bluff_pct = 0.0
        elif is_overfolder:
            bluff_pct = 0.56
        elif opp_fold < 0.42:
            bluff_pct = 0.08

        # On river, never turn medium showdown pairs (0.36..0.55) into bluffs; bluff missed draws with blockers
        has_blocker = any((c % 13) == 12 for c in hole_ids[:2])
        can_bluff = (0.12 <= equity <= 0.34 and (has_blocker or is_overfolder)) if nb == 5 else (equity >= 0.44)
        if can_bluff and rng.random() < bluff_pct:
            frac = max(0.30, (0.62 if nb == 5 else 0.38) + jitter * 0.5)
            target = int(opp_bet + pot * frac)
            bet_amt = max(min_raise, min(max_raise, target))
            if bet_amt >= min_raise:
                return ("raise", bet_amt)

    return ("check" if "check" in legal else "call", 0)


# ======================= protocol controller =======================

LOCK_IN = False          # once the match and the capped score are mathematically secured, stop risking chips
STAGE1_CAP = 400        # Rulebook 8.3 (provisional) - update here if the organisers change C
STAGE2_CAP = 1000

SUIT_MAP = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
RANK_MAP = {
    '2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
    '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12
}
STREET_MAP = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}


def _pair_strength(c1, c2):
    id1, id2 = parse_card_id(c1), parse_card_id(c2)
    r1, s1 = id1 % 13, id1 // 13
    r2, s2 = id2 % 13, id2 // 13
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


def _is_locked_in(net_chips, score_cap, hands_played, total_hands):
    if not LOCK_IN or score_cap <= 0:
        return False
    hands_rem = max(0, total_hands - hands_played)
    max_possible_loss = hands_rem * 2
    return (net_chips - max_possible_loss) >= (score_cap + 10)


def _compute_dynamic_budget_ms(time_left_ms, hands_played, total_hands, pot, street, is_discard=False):
    hands_rem = max(1, total_hands - hands_played)
    usable_ms = max(400.0, time_left_ms * 0.70)
    per_hand_ms = usable_ms / hands_rem
    base = per_hand_ms * (0.20 if is_discard else 0.32)
    if pot >= 60:
        base *= 1.45
    elif pot >= 24:
        base *= 1.20
    if street in ("turn", "river"):
        base *= 1.15
    lo, hi = (2.4, 6.0) if is_discard else (3.0, 9.5)
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
            for entry_idx, entry in enumerate(history):
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
                            if my_last_bet_street is None and entry_idx == 0:
                                # opponent acted first preflop, so it is the button facing my big blind
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
    __slots__ = ['hole', 'flop_board_ids', 'dead', 'opp_discard_id', 'is_button', 'opp_raised']

    def __init__(self):
        self.hole = []
        self.flop_board_ids = []
        self.dead = 0
        self.opp_discard_id = -1
        self.is_button = 0
        self.opp_raised = 0


def parse_card_id(card_str):
    s = card_str.strip()
    if len(s) == 3 and s[:2] == "10":
        s = "T" + s[2]
    return SUIT_MAP[s[1].lower()] * 13 + RANK_MAP[s[0].upper()]


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


def _fast_heuristic_discard(cards, board_cards):
    branks = {parse_card_id(c) % 13 for c in board_cards}
    bsuits = [parse_card_id(c) // 13 for c in board_cards]
    best_drop, best_sc = 0, -999
    for d in range(len(cards)):
        kept = [cards[i] for i in range(len(cards)) if i != d]
        if len(kept) < 2:
            continue
        sc = _pair_strength(kept[0], kept[1])
        for kc in kept:
            kid = parse_card_id(kc)
            if (kid % 13) in branks:
                sc += 180 + (kid % 13) * 10
            if bsuits.count(kid // 13) >= 2:
                sc += 35
        if sc > best_sc:
            best_sc, best_drop = sc, d
    return cards[best_drop]


def _fast_heuristic_action(req, hole):
    legal = req.get("legal_actions", [])
    board = req.get("board", [])
    pot = max(2, int(req.get("pot", 2)))
    to_call = int(req.get("to_call", 0))
    branks = {parse_card_id(c) % 13 for c in board}
    ranks = [parse_card_id(c) % 13 for c in hole]
    has_pair = (len(set(ranks)) < len(ranks))
    hits = sum(1 for r in ranks if r in branks)
    strong = (hits >= 2) or (has_pair and (hits >= 1 or (max(ranks) if ranks else 0) >= 9))
    playable = strong or hits >= 1 or (max(ranks) if ranks else 0) >= 11

    if to_call <= 0:
        if strong and "raise" in legal:
            return legalize_action(req, "raise", int(req.get("opp_bet", 0)) + pot // 2)
        return legalize_action(req, "check")
    if strong and to_call <= pot:
        return legalize_action(req, "call")
    if playable and to_call <= pot * 0.35:
        return legalize_action(req, "call")
    return legalize_action(req, "check" if "check" in legal else "fold")


def choose_discard(req, state, time_left_ms, hands_played=0, total_hands=400, net_chips=0, score_cap=400):
    cards = req.get("hole_cards", state.hole)
    if not cards:
        return {"type": "discard", "card": "2s"}
    board_cards = req.get("board", [])

    if _is_locked_in(net_chips, score_cap, hands_played, total_hands):
        return {"type": "discard", "card": _fast_heuristic_discard(cards, board_cards)}

    if len(board_cards) >= 3 and len(cards) >= 3 and time_left_ms > 1500:
        try:
            h_ids = [parse_card_id(c) for c in cards[:3]]
            b_ids = [parse_card_id(c) for c in board_cards[:3]]
            budget = _compute_dynamic_budget_ms(
                time_left_ms, hands_played, total_hands, int(req.get("pot", 6)), "flop", is_discard=True
            )
            drop_idx = py_choose_discard(h_ids, b_ids, state.dead, budget_ms=budget)
            if 0 <= drop_idx < len(cards):
                return {"type": "discard", "card": cards[drop_idx]}
        except Exception as e:
            sys.stderr.write(f"WARN: discard solver fallback ({e})\n")
            sys.stderr.flush()

    return {"type": "discard", "card": _fast_heuristic_discard(cards, board_cards)}


def choose_action(req, state, tracker, time_left_ms, score_cap, total_hands=400):
    legal = req.get("legal_actions", [])

    if _is_locked_in(tracker.net_chips, score_cap, tracker.hands, total_hands):
        return legalize_action(req, "check" if "check" in legal else "fold")

    if not state.hole or time_left_ms < 350:
        return _fast_heuristic_action(req, state.hole)

    try:
        street_name = req.get("street", "preflop")
        street_id = STREET_MAP.get(street_name, 0)
        pot = int(req.get("pot", 2))
        my_bet = int(req.get("my_bet", 0))
        opp_bet = int(req.get("opp_bet", 0))
        to_call = int(req.get("to_call", max(0, opp_bet - my_bet)))
        min_raise = int(req.get("min_raise", 0))
        max_raise = int(req.get("max_raise", 0))

        opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose = tracker.get_stats()
        h_ids = [parse_card_id(c) for c in state.hole[:3]]
        b_ids = [parse_card_id(c) for c in req.get("board", [])]

        budget = 0.35 if time_left_ms < 1800 else _compute_dynamic_budget_ms(
            time_left_ms, tracker.hands, total_hands, pot, street_name, is_discard=False
        )

        act, amt = py_choose_action(
            street_id, pot, to_call, my_bet, opp_bet, min_raise, max_raise, legal,
            h_ids, b_ids, state.flop_board_ids, state.dead, state.opp_discard_id,
            opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose,
            state.is_button, state.opp_raised, tracker.net_chips, score_cap,
            budget_ms=budget
        )
        return legalize_action(req, act, amt)
    except Exception as e:
        sys.stderr.write(f"WARN: action solver fallback ({e})\n")
        sys.stderr.flush()
        return _fast_heuristic_action(req, state.hole)


def _emergency_reply(msg, line, state):
    """Last-resort reply that can never raise: used when normal processing of a request failed."""
    try:
        mt = msg.get("type") if msg is not None else None
        if mt is None:
            mt = "discard_request" if '"discard_request"' in line else ("action_request" if '"action_request"' in line else None)
        if mt == "discard_request":
            hc = (msg or {}).get("hole_cards") or list(getattr(state, "hole", []) or [])
            if not hc:
                return {"type": "discard", "card": "2s"}
            try:
                return {"type": "discard", "card": _fast_heuristic_discard(hc, (msg or {}).get("board", []))}
            except Exception:
                return {"type": "discard", "card": min(hc, key=lambda c: RANK_MAP.get(str(c)[:1], 0))}
        if mt == "action_request":
            try:
                return _fast_heuristic_action(msg, (msg or {}).get("hole_cards", getattr(state, "hole", [])))
            except Exception:
                lg = (msg or {}).get("legal_actions") or []
                if "check" in lg:
                    return {"type": "action", "action": "check"}
                if "fold" in lg:
                    return {"type": "action", "action": "fold"}
                if "call" in lg:
                    return {"type": "action", "action": "call"}
                return {"type": "action", "action": "fold"}
    except Exception:
        pass
    return None


def main():
    gc.disable()
    current_state = LiveState()
    tracker = OpponentTracker()
    time_bank_ms = 60000.0
    total_spent_ms = 0.0
    total_hands = 400
    score_cap = STAGE1_CAP

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        t0 = time.perf_counter()
        msg = None
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                continue
            t = msg.get("type")
            reply = None

            if t == "init":
                current_state = LiveState()
                tracker = OpponentTracker()
                total_spent_ms = 0.0
                if "time_bank_ms" in msg:
                    time_bank_ms = float(msg["time_bank_ms"])
                total_hands = int(msg.get("total_hands", 500 if time_bank_ms > 45000 else 200))
                score_cap = STAGE2_CAP if (total_hands > 300 or time_bank_ms > 45000) else STAGE1_CAP
                _ensure_preflop_lut()
            elif t == "new_hand":
                current_state.hole = list(msg.get("hole_cards", []))
                current_state.flop_board_ids = []
                current_state.dead = 0
                current_state.opp_discard_id = -1
                current_state.opp_raised = 0
                seat = msg.get("seat")
                if seat == "button":
                    current_state.is_button = 1
                elif seat == "big_blind":
                    current_state.is_button = 0
                else:
                    current_state.is_button = 1 if (tracker.hands % 2 == 0) else 0
            elif t == "action_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                board_cards = msg.get("board", [])
                if len(board_cards) == 3 and not current_state.flop_board_ids:
                    current_state.flop_board_ids = [parse_card_id(c) for c in board_cards]

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
                if len(board_cards) == 3 and not current_state.flop_board_ids:
                    current_state.flop_board_ids = [parse_card_id(c) for c in board_cards]
                reply = choose_discard(
                    msg, current_state,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms)),
                    tracker.hands,
                    total_hands,
                    tracker.net_chips,
                    score_cap
                )
            elif t == "discard_result":
                my_discard = msg.get("my_discard")
                opp_discard = msg.get("opp_discard")
                if my_discard:
                    current_state.dead |= (1 << parse_card_id(my_discard))
                if opp_discard:
                    od_id = parse_card_id(opp_discard)
                    current_state.dead |= (1 << od_id)
                    current_state.opp_discard_id = od_id
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
            try:
                sys.stderr.write(f"ERROR: {str(e)}\n")
                sys.stderr.flush()
            except Exception:
                pass
            reply = _emergency_reply(msg if isinstance(msg, dict) else None, line, current_state)
            if reply is not None:
                try:
                    sys.stdout.write(json.dumps(reply) + '\n')
                    sys.stdout.flush()
                except Exception:
                    pass
            total_spent_ms += (time.perf_counter() - t0) * 1000.0


if __name__ == "__main__":
    main()
