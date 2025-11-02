import getpass
import math
import re
from collections import Counter

# Scoring rules (100 total)
# 1) Length: up to 30 pts
# 2) Variety (lower/upper/digit/symbol): up to 30 pts
# 3) Penalties (repeats, sequences, common patterns): -0..40 pts
# 4) Bonus for long+varied: up to 10 pts

SYMBOLS = r"!@#$%^&*()_+\-=\[\]{};':\",.<>/?\\|`~"
COMMON_PATTERNS = [
    "password", "qwerty", "abc", "abcd", "abc123", "letmein", "admin",
    "welcome", "iloveyou", "dragon", "monkey", "football", "baseball",
    "123", "1234", "12345", "123456", "0000", "1111", "2222"
]

def score_length(pw: str) -> int:
    # 8 chars → 10 pts, 12 → 20 pts, 16+ → 30 pts (cap at 30)
    if len(pw) >= 16: return 30
    if len(pw) >= 12: return 20
    if len(pw) >= 8:  return 10
    return max(0, len(pw) - 4)  # tiny credit for 5–7

def score_variety(pw: str) -> int:
    has_lower = any(c.islower() for c in pw)
    has_upper = any(c.isupper() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    has_symbol = any(c in SYMBOLS for c in pw)
    kinds = sum([has_lower, has_upper, has_digit, has_symbol])
    return [0, 10, 18, 24, 30][kinds]  # 0..30

def penalty_repeats(pw: str) -> int:
    # Penalize long runs of same char or very unbalanced characters
    # Run penalty: each streak >=3 costs 2*(streak-2)
    penalty = 0
    streak = 1
    for i in range(1, len(pw)):
        if pw[i] == pw[i-1]:
            streak += 1
        else:
            if streak >= 3:
                penalty += 2 * (streak - 2)
            streak = 1
    if streak >= 3:
        penalty += 2 * (streak - 2)

    # Frequency skew: if one char is >40% of password, small penalty
    if pw:
        counts = Counter(pw)
        most = counts.most_common(1)[0][1]
        if most / len(pw) > 0.4:
            penalty += 5
    return min(penalty, 20)

def penalty_sequences(pw: str) -> int:
    # Penalize obvious forward/backward sequences like 'abcd', '1234'
    penalty = 0
    lowers = "abcdefghijklmnopqrstuvwxyz"
    uppers = lowers.upper()
    digits = "0123456789"
    seqs = [lowers, uppers, digits, lowers[::-1], uppers[::-1], digits[::-1]]

    pw_low = pw.lower()
    for s in seqs:
        for k in range(4, 8):  # sequences of length 4..7
            for i in range(0, len(s) - k + 1):
                if s[i:i+k] in pw_low:
                    penalty += 3  # small per match
    return min(penalty, 12)

def penalty_common_patterns(pw: str) -> int:
    pw_low = pw.lower()
    pen = 0
    for pat in COMMON_PATTERNS:
        if pat in pw_low:
            pen += 6
    # Keyboard rows (rough)
    keyboard_rows = ["qwerty", "asdf", "zxcv", "1q2w3e", "qaz", "wasd"]
    for row in keyboard_rows:
        if row in pw_low or row[::-1] in pw_low:
            pen += 6
    # Date-like patterns (YYYY, DDMM, MMDD, 19xx/20xx)
    if re.search(r"(19|20)\d{2}", pw_low): pen += 5
    if re.search(r"\b(0?[1-9]|1[0-2])[-/\.]?(0?[1-9]|[12]\d|3[01])\b", pw_low): pen += 5
    return min(pen, 20)

def bonus_strong_mix(pw: str) -> int:
    if len(pw) >= 14 and score_variety(pw) >= 24:
        return 10
    return 0

def estimate_entropy_bits(pw: str) -> float:
    # Very rough entropy estimate from char set size.
    charset = 0
    if any(c.islower() for c in pw): charset += 26
    if any(c.isupper() for c in pw): charset += 26
    if any(c.isdigit() for c in pw): charset += 10
    if any(c in SYMBOLS for c in pw): charset += len(SYMBOLS)
    if charset == 0: return 0.0
    return round(len(pw) * math.log2(charset), 1)

def strength_label(score: int) -> str:
    if score >= 85: return "Very Strong ✅"
    if score >= 70: return "Strong ✅"
    if score >= 55: return "Medium ⚠️"
    if score >= 35: return "Weak ❌"
    return "Very Weak ❌"

def tips(pw: str) -> list[str]:
    t = []
    if len(pw) < 12: t.append("Use at least 12 characters.")
    if not any(c.islower() for c in pw): t.append("Add lowercase letters.")
    if not any(c.isupper() for c in pw): t.append("Add uppercase letters.")
    if not any(c.isdigit() for c in pw): t.append("Add digits.")
    if not any(c in SYMBOLS for c in pw): t.append("Add symbols.")
    if penalty_repeats(pw) > 0: t.append("Avoid long repeats like 'aaa' or '!!!!'.")
    if penalty_sequences(pw) > 0: t.append("Avoid sequences like 'abcd' or '1234'.")
    if penalty_common_patterns(pw) > 0: t.append("Avoid common words, keyboard rows, or dates.")
    if len(t) == 0:
        t.append("Nice! Consider a passphrase: 3–4 random words with a symbol.")
    return t

def score_password(pw: str) -> dict:
    s_len = score_length(pw)
    s_var = score_variety(pw)
    p_rep = penalty_repeats(pw)
    p_seq = penalty_sequences(pw)
    p_pat = penalty_common_patterns(pw)
    bonus = bonus_strong_mix(pw)

    raw = s_len + s_var + bonus - (p_rep + p_seq + p_pat)
    score = max(0, min(100, raw))

    return {
        "score": int(score),
        "label": strength_label(score),
        "entropy_bits": estimate_entropy_bits(pw),
        "breakdown": {
            "length": s_len, "variety": s_var, "bonus": bonus,
            "penalty_repeats": p_rep, "penalty_sequences": p_seq, "penalty_patterns": p_pat
        },
        "tips": tips(pw),
    }

def main():
    print("=== Password Strength Checker ===")
    choice = input("Hide input? (Y/n): ").strip().lower()
    if choice in ("", "y", "yes"):
        pw = getpass.getpass("Enter password: ")
    else:
        pw = input("Enter password: ")

    result = score_password(pw)
    print(f"\nScore: {result['score']} / 100  -> {result['label']}")
    print(f"Estimated entropy: {result['entropy_bits']} bits (rough)")
    b = result["breakdown"]
    print(f"Breakdown: length+variety+bonus = {b['length']} + {b['variety']} + {b['bonus']}, "
          f"penalties = -{b['penalty_repeats']}-{-b['penalty_sequences']}-{-b['penalty_patterns']}")
    print("\nTips:")
    for tip in result["tips"]:
        print(f" • {tip}")

if __name__ == "__main__":
    main()
