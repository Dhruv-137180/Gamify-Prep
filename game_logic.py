"""Pure game-rule functions.  No DB, no UI — just math."""
import math

# §2.1 EXP / Gold tables
EXP_TABLE  = {"PROJECT": 50, "THEORY": 30, "SKILL": 30, "COMBO": 40}
GOLD_TABLE = {"PROJECT": 20, "THEORY": 10, "SKILL": 10, "COMBO": 30}

# §2.3 Rank thresholds (highest first so the loop short-circuits early)
RANK_THRESHOLDS = [
    (60, "S-RANK", "S-Rank Monarch"),
    (45, "A-RANK", "A-Rank Elite"),
    (30, "B-RANK", "B-Rank Hunter"),
    (20, "C-RANK", "C-Rank Hunter"),
    (10, "D-RANK", "D-Rank Awakened"),
    ( 1, "E-RANK", "E-Rank Garbage"),
]

# §2.4 Skill rank thresholds
SKILL_RANK_THRESHOLDS = [
    (750, "S"), (520, "A"), (350, "B"),
    (220, "C"), (120, "D"), ( 50, "E"), (0, "F"),
]


def next_level_exp(level: int) -> int:
    """§2.2  floor(100 * level^1.5)"""
    return math.floor(100 * (level ** 1.5))


def get_rank_info(level: int):
    """Returns (rank_str, title_str) derived from level.  §2.3"""
    for threshold, rank, title in RANK_THRESHOLDS:
        if level >= threshold:
            return rank, title
    return "E-RANK", "E-Rank Garbage"


def get_skill_rank(points: int) -> str:
    """§2.4"""
    for threshold, rank in SKILL_RANK_THRESHOLDS:
        if points >= threshold:
            return rank
    return "F"


def apply_exp_gain(level: int, current_exp: int, gained: int):
    """
    Adds gained EXP and handles multi-level gains.
    Returns (new_level, remaining_exp, new_next_level_exp).  §2.2
    """
    current_exp += gained
    while True:
        threshold = next_level_exp(level)
        if current_exp >= threshold:
            current_exp -= threshold
            level += 1
        else:
            break
    return level, current_exp, next_level_exp(level)


# ── Achievements ───────────────────────────────────────────────────────────────

ACHIEVEMENTS = [
    {"id": "first_quest",  "name": "AWAKENING",       "desc": "Complete your first quest",       "icon": "⚡"},
    {"id": "streak_3",     "name": "MOMENTUM",         "desc": "Reach a 3-day streak",            "icon": "🔥"},
    {"id": "streak_7",     "name": "DEDICATED",        "desc": "Reach a 7-day streak",            "icon": "🔥"},
    {"id": "streak_14",    "name": "RELENTLESS",       "desc": "Reach a 14-day streak",           "icon": "🔥"},
    {"id": "streak_30",    "name": "UNSTOPPABLE",      "desc": "Reach a 30-day streak",           "icon": "🔥"},
    {"id": "level_10",     "name": "NOVICE HUNTER",    "desc": "Reach Level 10",                  "icon": "⬆"},
    {"id": "level_25",     "name": "SEASONED HUNTER",  "desc": "Reach Level 25",                  "icon": "⬆"},
    {"id": "level_50",     "name": "ELITE HUNTER",     "desc": "Reach Level 50",                  "icon": "⬆"},
    {"id": "rank_d",       "name": "D-RANK AWAKENED",  "desc": "Reach D-Rank",                    "icon": "🏆"},
    {"id": "rank_c",       "name": "C-RANK HUNTER",    "desc": "Reach C-Rank",                    "icon": "🏆"},
    {"id": "rank_b",       "name": "B-RANK HUNTER",    "desc": "Reach B-Rank",                    "icon": "🏆"},
    {"id": "rank_a",       "name": "A-RANK ELITE",     "desc": "Reach A-Rank",                    "icon": "🏆"},
    {"id": "rank_s",       "name": "S-RANK MONARCH",   "desc": "Reach S-Rank",                    "icon": "👑"},
    {"id": "skill_rank_a", "name": "SPECIALIST",       "desc": "Reach A-rank in any skill",       "icon": "⭐"},
    {"id": "skill_rank_s", "name": "GRANDMASTER",      "desc": "Reach S-rank in any skill",       "icon": "⭐"},
    {"id": "all_skills_c", "name": "WELL-ROUNDED",     "desc": "All skills at C-rank or higher",  "icon": "⭐"},
    {"id": "first_combo",  "name": "COMBO KING",       "desc": "Complete all quests in one day",  "icon": "⚡"},
    {"id": "gold_1000",    "name": "WEALTHY",          "desc": "Accumulate 1000 Gold total",      "icon": "💰"},
    {"id": "boss_first",   "name": "BOSS SLAYER",      "desc": "Complete a Boss Battle",          "icon": "⚔"},
    {"id": "boss_5",       "name": "BOSS HUNTER",      "desc": "Complete 5 Boss Battles",         "icon": "⚔"},
]

_RANK_ORDER       = {"E-RANK": 0, "D-RANK": 1, "C-RANK": 2, "B-RANK": 3, "A-RANK": 4, "S-RANK": 5}
_SKILL_RANK_ORDER = {"F": 0, "E": 1, "D": 2, "C": 3, "B": 4, "A": 5, "S": 6}


def get_achievable_ids(hunter: dict, skills: list,
                       combo_today: bool = False, boss_count: int = 0) -> list:
    """Returns achievement IDs whose unlock conditions are currently met."""
    result  = []
    level   = hunter.get("level", 0)
    gold    = hunter.get("gold", 0)
    streak  = hunter.get("streak", 0)
    rank, _ = get_rank_info(level)
    rank_v  = _RANK_ORDER.get(rank, 0)

    if gold > 0 or level > 1:
        result.append("first_quest")

    for days, aid in [(3, "streak_3"), (7, "streak_7"), (14, "streak_14"), (30, "streak_30")]:
        if streak >= days:
            result.append(aid)

    for lvl, aid in [(10, "level_10"), (25, "level_25"), (50, "level_50")]:
        if level >= lvl:
            result.append(aid)

    for req, aid in [(1, "rank_d"), (2, "rank_c"), (3, "rank_b"), (4, "rank_a"), (5, "rank_s")]:
        if rank_v >= req:
            result.append(aid)

    sranks = [s.get("current_rank", "F") for s in skills]
    if any(_SKILL_RANK_ORDER.get(r, 0) >= 5 for r in sranks):
        result.append("skill_rank_a")
    if any(_SKILL_RANK_ORDER.get(r, 0) >= 6 for r in sranks):
        result.append("skill_rank_s")
    if sranks and all(_SKILL_RANK_ORDER.get(r, 0) >= 3 for r in sranks):
        result.append("all_skills_c")

    if combo_today:
        result.append("first_combo")
    if gold >= 1000:
        result.append("gold_1000")
    if boss_count >= 1:
        result.append("boss_first")
    if boss_count >= 5:
        result.append("boss_5")

    return result


# ── Side Quests ────────────────────────────────────────────────────────────────

SIDE_QUEST_POOL = [
    {"name": "Write a parameterized async FIFO in SV",       "category": "PROJECT", "exp": 25, "gold": 12},
    {"name": "Implement an APB slave state machine",          "category": "PROJECT", "exp": 25, "gold": 12},
    {"name": "Simulate a 4-bit ripple carry adder",           "category": "PROJECT", "exp": 20, "gold": 10},
    {"name": "Write a reusable APB VIP from scratch",         "category": "PROJECT", "exp": 30, "gold": 15},
    {"name": "Implement a UVM driver + sequencer pair",       "category": "PROJECT", "exp": 30, "gold": 15},
    {"name": "Study: CDC synchronizer types and trade-offs",  "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Study: UVM factory override mechanism",         "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Study: SVA implication operators (|-> vs |=>)", "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Study: AHB burst types and pipelining",         "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Study: Gray code and FIFO pointer arithmetic",  "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Study: UVM RAL model structure",                "category": "THEORY",  "exp": 20, "gold":  8},
    {"name": "Study: Formal k-induction vs BMC",              "category": "THEORY",  "exp": 20, "gold":  8},
    {"name": "Practice: Write 3 SV constraint blocks",        "category": "SKILL",   "exp": 20, "gold":  9},
    {"name": "Practice: Write 5 SVA concurrent assertions",   "category": "SKILL",   "exp": 20, "gold":  9},
    {"name": "Practice: Set up a UVM coverage group",         "category": "SKILL",   "exp": 20, "gold":  9},
    {"name": "Practice: Write a UVM sequence with p_sequencer","category": "SKILL",   "exp": 25, "gold": 10},
    {"name": "Practice: Implement a scoreboard in UVM",       "category": "SKILL",   "exp": 25, "gold": 10},
    {"name": "Practice: Create a complete UVM test environment","category": "SKILL",  "exp": 30, "gold": 12},
    {"name": "Practice: Solve a formal vacuity bug",          "category": "SKILL",   "exp": 20, "gold":  9},
    {"name": "Practice: Write cross coverage for a DMA block","category": "SKILL",   "exp": 20, "gold":  9},
    {"name": "Explain CDC to a junior engineer (out loud)",   "category": "SKILL",   "exp": 15, "gold":  7},
    {"name": "Draw the UVM component hierarchy from memory",  "category": "SKILL",   "exp": 15, "gold":  7},
    {"name": "Trace an AXI read transaction cycle by cycle",  "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Write a Python script to parse sim logs",       "category": "PROJECT", "exp": 20, "gold": 10},
    {"name": "Map an APB register block to UVM RAL",          "category": "SKILL",   "exp": 25, "gold": 10},
    {"name": "Analyse a failing assertion CEX trace",         "category": "SKILL",   "exp": 20, "gold":  9},
    {"name": "Review OVM→UVM migration notes",                "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Implement a virtual sequence for multi-agent",  "category": "PROJECT", "exp": 30, "gold": 14},
    {"name": "Study: SV class inheritance chain in UVM",      "category": "THEORY",  "exp": 15, "gold":  7},
    {"name": "Practice: Write $past/$rose/$fell assertions",  "category": "SKILL",   "exp": 15, "gold":  7},
]


def get_daily_side_quests(date_str: str, count: int = 3) -> list:
    """Returns a deterministic list of side quests for the given date."""
    import hashlib
    import random as _rnd
    seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    rng  = _rnd.Random(seed)
    chosen = rng.sample(SIDE_QUEST_POOL, min(count, len(SIDE_QUEST_POOL)))
    return [dict(q, quest_key=f"{date_str}_{i}") for i, q in enumerate(chosen)]


# ── Prestige ───────────────────────────────────────────────────────────────────

PRESTIGE_TITLES = [
    "Shadow Monarch",
    "Absolute Being",
    "Ruler of Death",
    "Sovereign of Chaos",
    "Monarch of Destruction",
    "Architect of Fate",
    "God of the System",
]


def get_prestige_title(prestige_count: int) -> str:
    if prestige_count <= 0:
        return ""
    idx = min(prestige_count - 1, len(PRESTIGE_TITLES) - 1)
    return PRESTIGE_TITLES[idx]
