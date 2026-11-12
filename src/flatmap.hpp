#pragma once
#include <vector>
#include <cstdint>
#include <limits>

constexpr uint64_t EMPTY_KEY = std::numeric_limits<uint64_t>::max();

inline uint64_t mix(uint64_t k) {
    k ^= k >> 33;
    k *= 0xff51afd7ed558ccdULL;
    k ^= k >> 33;
    k *= 0xc4ceb9fe1a85ec53ULL;
    k ^= k >> 33;
    return k;
}

struct FlatMap {
    std::vector<uint64_t> keys;
    std::vector<uint32_t> vals;
    uint64_t mask;
    uint32_t count;

    FlatMap(size_t capacity = 1048576) {
        keys.resize(capacity, EMPTY_KEY);
        vals.resize(capacity, 0);
        mask = capacity - 1;
        count = 0;
    }

    uint32_t* find(uint64_t k) {
        uint64_t start = mix(k) & mask;
        for (uint64_t step = 0; step <= mask; ++step) {
            uint64_t i = (start + step) & mask;
            if (keys[i] == k) return &vals[i];
            if (keys[i] == EMPTY_KEY) return nullptr;
        }
        return nullptr;
    }

    bool insert(uint64_t k, uint32_t v) {
        if (count >= (mask * 3) / 4) return false;
        uint64_t start = mix(k) & mask;
        for (uint64_t step = 0; step <= mask; ++step) {
            uint64_t i = (start + step) & mask;
            if (keys[i] == k) {
                vals[i] = v;
                return true;
            }
            if (keys[i] == EMPTY_KEY) {
                keys[i] = k;
                vals[i] = v;
                count++;
                return true;
            }
        }
        return false;
    }
};