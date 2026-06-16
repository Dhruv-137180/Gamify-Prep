"""All SQLite access.  One connection per call (no pooling needed for a single-user desktop app)."""
import sqlite3
import os
from datetime import date, timedelta, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hunter.db")

SKILLS = [
    "Python", "Constraints", "Assertions", "Covergroups",
    "Formal", "UVM", "OOPS", "CDC", "Testplan",
]


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


# ── Schema + seed ─────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables and seed initial rows.  Safe to call on every launch."""
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS hunter_stats (
                hunter_id      INTEGER PRIMARY KEY,
                player_name    TEXT    DEFAULT 'PARIN MISTRY',
                level          INTEGER DEFAULT 1,
                current_exp    INTEGER DEFAULT 0,
                next_level_exp INTEGER DEFAULT 100,
                gold           INTEGER DEFAULT 0,
                title          TEXT    DEFAULT 'E-Rank Garbage',
                streak         INTEGER DEFAULT 0,
                best_streak    INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS quest_log (
                date              TEXT PRIMARY KEY,
                project_completed INTEGER DEFAULT 0,
                theory_completed  INTEGER DEFAULT 0,
                skill_completed   INTEGER DEFAULT 0,
                skill_name        TEXT,
                penalty_triggered INTEGER DEFAULT 0,
                exp_awarded       INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS dv_skills (
                skill_name         TEXT PRIMARY KEY,
                proficiency_points INTEGER DEFAULT 0,
                current_rank       TEXT    DEFAULT 'F'
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        c.execute("INSERT OR IGNORE INTO hunter_stats (hunter_id) VALUES (1)")

        for skill in SKILLS:
            c.execute("INSERT OR IGNORE INTO dv_skills (skill_name) VALUES (?)", (skill,))

        today = date.today().isoformat()
        for key, val in [
            ("last_reset_date",    today),
            ("volume",             "0.70"),
            ("muted",              "0"),
            ("penalty_deadline",   ""),
            ("theme",              "cyan"),
            ("streak_shield",      "0"),
            ("reminder_enabled",   "1"),
            ("reminder_hour",      "20"),
        ]:
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    _init_achievements()
    _init_shop()
    _init_boss()
    _init_skill_goals()
    _init_session_notes()
    _init_side_quests()
    _init_pomodoro()
    _init_resources()
    _init_concepts()
    _init_prestige()


def reset_db() -> None:
    """Wipe everything and re-seed."""
    with _conn() as c:
        c.executescript("""
            DROP TABLE IF EXISTS hunter_stats;
            DROP TABLE IF EXISTS quest_log;
            DROP TABLE IF EXISTS dv_skills;
            DROP TABLE IF EXISTS settings;
            DROP TABLE IF EXISTS tasks;
            DROP TABLE IF EXISTS task_completions;
            DROP TABLE IF EXISTS achievements;
            DROP TABLE IF EXISTS shop_inventory;
            DROP TABLE IF EXISTS active_boosts;
            DROP TABLE IF EXISTS boss_battles;
            DROP TABLE IF EXISTS skill_goals;
            DROP TABLE IF EXISTS session_notes;
            DROP TABLE IF EXISTS side_quest_completions;
            DROP TABLE IF EXISTS pomodoro_sessions;
            DROP TABLE IF EXISTS study_resources;
            DROP TABLE IF EXISTS concepts;
            DROP TABLE IF EXISTS concept_attempts;
            DROP TABLE IF EXISTS prestige_log;
        """)
    init_db()
    migrate_tasks()


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with _conn() as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))


# ── Hunter stats ──────────────────────────────────────────────────────────────

def get_hunter() -> dict:
    with _conn() as c:
        row = c.execute("SELECT * FROM hunter_stats WHERE hunter_id = 1").fetchone()
        return dict(row) if row else {}


def update_hunter(**kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    with _conn() as c:
        c.execute(f"UPDATE hunter_stats SET {fields} WHERE hunter_id = 1",
                  list(kwargs.values()))


# ── Quest log ─────────────────────────────────────────────────────────────────

def get_or_create_quest_log(date_str: str) -> dict:
    with _conn() as c:
        row = c.execute("SELECT * FROM quest_log WHERE date = ?", (date_str,)).fetchone()
        if row is None:
            c.execute("INSERT OR IGNORE INTO quest_log (date) VALUES (?)", (date_str,))
            row = c.execute("SELECT * FROM quest_log WHERE date = ?", (date_str,)).fetchone()
        return dict(row)


def get_quest_log(date_str: str) -> dict:
    with _conn() as c:
        row = c.execute("SELECT * FROM quest_log WHERE date = ?", (date_str,)).fetchone()
        return dict(row) if row else {}


def update_quest_log(date_str: str, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [date_str]
    with _conn() as c:
        c.execute(f"UPDATE quest_log SET {fields} WHERE date = ?", vals)


def get_quest_logs_range(start: str, end: str) -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM quest_log WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Skills ────────────────────────────────────────────────────────────────────

def get_all_skills() -> list:
    with _conn() as c:
        rows = c.execute("SELECT * FROM dv_skills ORDER BY skill_name").fetchall()
        return [dict(r) for r in rows]


def update_skill(skill_name: str, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [skill_name]
    with _conn() as c:
        c.execute(f"UPDATE dv_skills SET {fields} WHERE skill_name = ?", vals)


# ── Tasks (new schema) ────────────────────────────────────────────────────────

_EXP_CAT  = {"PROJECT": 50, "THEORY": 30, "SKILL": 30, "CUSTOM": 30}
_GOLD_CAT = {"PROJECT": 20, "THEORY": 10, "SKILL": 10, "CUSTOM": 10}


def migrate_tasks() -> None:
    """Add tasks / task_completions tables and seed defaults. Safe to run every launch."""
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                category    TEXT    DEFAULT 'CUSTOM',
                exp_reward  INTEGER DEFAULT 30,
                gold_reward INTEGER DEFAULT 10,
                is_active   INTEGER DEFAULT 1,
                sort_order  INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS task_completions (
                task_id     INTEGER NOT NULL,
                date        TEXT    NOT NULL,
                skill_name  TEXT,
                pts_awarded INTEGER DEFAULT 0,
                PRIMARY KEY (task_id, date)
            );
        """)

    # Safe column upgrades for existing databases
    with _conn() as c:
        existing = {r[1] for r in c.execute("PRAGMA table_info(task_completions)").fetchall()}
        if "skill_name"  not in existing:
            c.execute("ALTER TABLE task_completions ADD COLUMN skill_name TEXT")
        if "pts_awarded" not in existing:
            c.execute("ALTER TABLE task_completions ADD COLUMN pts_awarded INTEGER DEFAULT 0")

    with _conn() as c:
        for task_id, name, cat, exp, gold, ord_ in [
            (1, "Execute Daily Target Block",   "PROJECT", 50, 20, 0),
            (2, "Master Theory / Architecture", "THEORY",  30, 10, 1),
            (3, "Practice DV Skill",            "SKILL",   30, 10, 2),
        ]:
            c.execute(
                "INSERT OR IGNORE INTO tasks (task_id, name, category, exp_reward, gold_reward, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, name, cat, exp, gold, ord_),
            )


def get_tasks() -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM tasks WHERE is_active = 1 ORDER BY sort_order, task_id"
        ).fetchall()
        return [dict(r) for r in rows]


def add_task(name: str, category: str = "CUSTOM") -> None:
    cat  = category if category in _EXP_CAT else "CUSTOM"
    with _conn() as c:
        max_ord = c.execute(
            "SELECT COALESCE(MAX(sort_order), 0) FROM tasks WHERE is_active = 1"
        ).fetchone()[0]
        c.execute(
            "INSERT INTO tasks (name, category, exp_reward, gold_reward, sort_order) VALUES (?,?,?,?,?)",
            (name.strip(), cat, _EXP_CAT[cat], _GOLD_CAT[cat], max_ord + 1),
        )


def remove_task(task_id: int) -> None:
    with _conn() as c:
        c.execute("UPDATE tasks SET is_active = 0 WHERE task_id = ?", (task_id,))


def get_today_completions(date_str: str) -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT task_id FROM task_completions WHERE date = ?", (date_str,)
        ).fetchall()
        return [r[0] for r in rows]


def update_task(task_id: int, name: str = None, category: str = None) -> None:
    fields, vals = [], []
    if name is not None:
        fields.append("name = ?"); vals.append(name.strip())
    if category is not None and category in _EXP_CAT:
        fields.append("category = ?");    vals.append(category)
        fields.append("exp_reward = ?");  vals.append(_EXP_CAT[category])
        fields.append("gold_reward = ?"); vals.append(_GOLD_CAT[category])
    if not fields:
        return
    vals.append(task_id)
    with _conn() as c:
        c.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE task_id = ?", vals)


def complete_task(task_id: int, skill_name: str = None) -> dict:
    from game_logic import apply_exp_gain, get_rank_info, get_skill_rank

    today = date.today().isoformat()

    with _conn() as c:
        task = c.execute(
            "SELECT * FROM tasks WHERE task_id = ? AND is_active = 1", (task_id,)
        ).fetchone()
        if not task:
            return {"success": False}
        task = dict(task)
        if c.execute(
            "SELECT 1 FROM task_completions WHERE task_id = ? AND date = ?", (task_id, today)
        ).fetchone():
            return {"success": False, "alreadyDone": True}

    # Determine which skill to credit
    target_skill = skill_name
    if not target_skill and task["category"] == "SKILL":
        with _conn() as c:
            w = c.execute(
                "SELECT skill_name FROM dv_skills ORDER BY proficiency_points ASC LIMIT 1"
            ).fetchone()
            if w:
                target_skill = w["skill_name"]
    pts_to_award = (10 if task["category"] == "SKILL" else 5) if target_skill else 0

    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO task_completions (task_id, date, skill_name, pts_awarded) VALUES (?,?,?,?)",
            (task_id, today, target_skill, pts_to_award),
        )

    h         = get_hunter()
    exp_gain  = task["exp_reward"]
    gold_gain = task["gold_reward"]
    old_level = h["level"]
    old_rank  = get_rank_info(old_level)[0]

    new_lvl, new_exp, new_nxt = apply_exp_gain(h["level"], h["current_exp"], exp_gain)
    update_hunter(level=new_lvl, current_exp=new_exp, next_level_exp=new_nxt,
                  gold=h["gold"] + gold_gain, title=get_rank_info(new_lvl)[1])

    # Combo check
    active   = get_tasks()
    done_ids = get_today_completions(today)
    all_done = bool(active) and all(t["task_id"] in done_ids for t in active)

    combo_exp = combo_gold = 0
    if all_done:
        combo_exp, combo_gold = 40, 30
        h2 = get_hunter()
        l2, e2, n2 = apply_exp_gain(h2["level"], h2["current_exp"], combo_exp)
        new_streak = h2["streak"] + 1
        update_hunter(level=l2, current_exp=e2, next_level_exp=n2,
                      gold=h2["gold"] + combo_gold, streak=new_streak,
                      best_streak=max(h2["best_streak"], new_streak),
                      title=get_rank_info(l2)[1])
        clear_penalty()

    # Award skill proficiency
    if target_skill and pts_to_award > 0:
        with _conn() as c:
            row = c.execute(
                "SELECT proficiency_points FROM dv_skills WHERE skill_name = ?", (target_skill,)
            ).fetchone()
            if row:
                pts  = row[0] + pts_to_award
                rank = get_skill_rank(pts)
                c.execute(
                    "UPDATE dv_skills SET proficiency_points=?, current_rank=? WHERE skill_name=?",
                    (pts, rank, target_skill),
                )

    final    = get_hunter()
    new_rank = get_rank_info(final["level"])[0]
    return {
        "success":         True,
        "expGained":       exp_gain,
        "goldGained":      gold_gain,
        "comboBonus":      all_done,
        "comboExpGained":  combo_exp,
        "comboGoldGained": combo_gold,
        "leveled":         final["level"] > old_level,
        "oldLevel":        old_level,
        "newLevel":        final["level"],
        "oldRank":         old_rank,
        "newRank":         new_rank,
        "skillCredited":   target_skill,
        "state":           get_full_state(),
    }


def uncomplete_task(task_id: int) -> dict:
    from game_logic import get_skill_rank
    today = date.today().isoformat()

    with _conn() as c:
        row = c.execute(
            "SELECT tc.skill_name, tc.pts_awarded, t.exp_reward, t.gold_reward "
            "FROM task_completions tc JOIN tasks t ON tc.task_id = t.task_id "
            "WHERE tc.task_id = ? AND tc.date = ?",
            (task_id, today),
        ).fetchone()
        if not row:
            return {"success": False}
        skill_name  = row[0]
        pts_awarded = row[1] or 0
        exp_reward  = row[2]
        gold_reward = row[3]
        c.execute(
            "DELETE FROM task_completions WHERE task_id = ? AND date = ?", (task_id, today)
        )

    h = get_hunter()
    update_hunter(
        current_exp=max(0, h["current_exp"] - exp_reward),
        gold=max(0, h["gold"] - gold_reward),
    )

    if skill_name and pts_awarded > 0:
        with _conn() as c:
            sr = c.execute(
                "SELECT proficiency_points FROM dv_skills WHERE skill_name = ?", (skill_name,)
            ).fetchone()
            if sr:
                pts  = max(0, sr[0] - pts_awarded)
                rank = get_skill_rank(pts)
                c.execute(
                    "UPDATE dv_skills SET proficiency_points=?, current_rank=? WHERE skill_name=?",
                    (pts, rank, skill_name),
                )

    return {"success": True, "state": get_full_state()}


def get_day_logs(date_str: str) -> dict:
    with _conn() as c:
        rows = c.execute(
            "SELECT tc.task_id, tc.skill_name, tc.pts_awarded, "
            "t.name, t.category, t.exp_reward, t.gold_reward "
            "FROM task_completions tc "
            "LEFT JOIN tasks t ON tc.task_id = t.task_id "
            "WHERE tc.date = ? ORDER BY tc.task_id",
            (date_str,),
        ).fetchall()
    return {
        "date":        date_str,
        "completions": [dict(r) for r in rows],
    }


def get_month_logs(year: int, month: int) -> list:
    import calendar as _cal
    days_in_month = _cal.monthrange(year, month)[1]
    today_str     = date.today().isoformat()
    result = []
    for day_num in range(1, days_in_month + 1):
        date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
        with _conn() as c:
            completed = c.execute(
                "SELECT COUNT(*) FROM task_completions WHERE date = ?", (date_str,)
            ).fetchone()[0]
            total = c.execute(
                "SELECT COUNT(*) FROM tasks WHERE is_active = 1"
            ).fetchone()[0]
        result.append({
            "date":     date_str,
            "day":      day_num,
            "completed": completed,
            "total":    total,
            "isToday":  date_str == today_str,
            "isPast":   date_str < today_str,
            "isFuture": date_str > today_str,
        })
    return result


def get_week_logs() -> list:
    today      = date.today()
    active     = get_tasks()
    task_ids   = [t["task_id"] for t in active]
    days       = []
    for i in range(6, -1, -1):
        d        = today - timedelta(days=i)
        date_str = d.isoformat()
        completed = 0
        if task_ids:
            ph = ",".join("?" * len(task_ids))
            with _conn() as c:
                completed = c.execute(
                    f"SELECT COUNT(*) FROM task_completions WHERE date=? AND task_id IN ({ph})",
                    [date_str] + task_ids,
                ).fetchone()[0]
        days.append({
            "date":      date_str,
            "dayName":   d.strftime("%a").upper(),
            "completed": completed,
            "total":     len(task_ids),
            "isToday":   i == 0,
        })
    return days


def uncomplete_quest_log(quest_type: str, date_str: str) -> dict:
    """Undo a quest completion — subtracts base EXP/Gold and clears the flag."""
    from game_logic import EXP_TABLE, GOLD_TABLE
    col_map = {"PROJECT": "project_completed",
               "THEORY":  "theory_completed",
               "SKILL":   "skill_completed"}
    col = col_map.get(quest_type)
    if not col:
        return {"success": False}

    log = get_quest_log(date_str)
    if not log or not log.get(col):
        return {"success": False, "message": "Quest not completed"}

    all_done = (log.get("project_completed") and
                log.get("theory_completed")  and
                log.get("skill_completed"))

    exp_to_remove  = EXP_TABLE.get(quest_type, 0)
    gold_to_remove = GOLD_TABLE.get(quest_type, 0)
    if all_done:
        exp_to_remove  += EXP_TABLE.get("COMBO", 0)
        gold_to_remove += GOLD_TABLE.get("COMBO", 0)

    update_quest_log(date_str, **{col: 0})

    h = get_hunter()
    new_streak = max(0, h["streak"] - 1) if all_done else h["streak"]
    update_hunter(
        current_exp=max(0, h["current_exp"] - exp_to_remove),
        gold=max(0, h["gold"] - gold_to_remove),
        streak=new_streak,
    )
    return {"success": True}


def get_penalty_state() -> dict:
    dl = get_setting("penalty_deadline", "")
    if not dl:
        return {"active": False}
    try:
        rem = (datetime.fromisoformat(dl) - datetime.now()).total_seconds()
        if rem <= 0:
            set_setting("penalty_deadline", "")
            return {"active": False}
        return {"active": True, "remainingSeconds": int(rem)}
    except Exception:
        return {"active": False}


def clear_penalty() -> None:
    set_setting("penalty_deadline", "")


def check_rollover() -> dict:
    today      = date.today().isoformat()
    last_reset = get_setting("last_reset_date", today)
    if today <= last_reset:
        return {"rolledOver": False}

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    active    = get_tasks()
    task_ids  = [t["task_id"] for t in active]
    y_done: list = []
    if task_ids:
        ph = ",".join("?" * len(task_ids))
        with _conn() as c:
            y_done = [r[0] for r in c.execute(
                f"SELECT task_id FROM task_completions WHERE date=? AND task_id IN ({ph})",
                [yesterday] + task_ids,
            ).fetchall()]

    all_done    = bool(active) and all(t["task_id"] in y_done for t in active)
    penalty_set = False
    penalty_sec = 0

    if not all_done and active:
        dl = (datetime.now() + timedelta(seconds=45 * 60)).isoformat()
        set_setting("penalty_deadline", dl)
        penalty_set = True
        penalty_sec = 45 * 60
        update_hunter(streak=0)

    set_setting("last_reset_date", today)
    return {"rolledOver": True, "penaltySet": penalty_set, "penaltySeconds": penalty_sec}


def get_full_state() -> dict:
    today = date.today().isoformat()
    return {
        "hunter":           get_hunter(),
        "tasks":            get_tasks(),
        "todayCompletions": get_today_completions(today),
        "skills":           get_all_skills(),
        "weekLogs":         get_week_logs(),
        "penalty":          get_penalty_state(),
        "settings": {
            "volume": get_setting("volume", "0.70"),
            "muted":  get_setting("muted",  "0"),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Achievements
# ═══════════════════════════════════════════════════════════════════════════════

def _init_achievements() -> None:
    from game_logic import ACHIEVEMENTS
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id TEXT PRIMARY KEY,
                unlocked       INTEGER DEFAULT 0,
                unlocked_date  TEXT    DEFAULT ''
            )
        """)
        for a in ACHIEVEMENTS:
            c.execute(
                "INSERT OR IGNORE INTO achievements (achievement_id) VALUES (?)",
                (a["id"],),
            )


def get_achievements() -> list:
    try:
        with _conn() as c:
            return [dict(r) for r in
                    c.execute("SELECT * FROM achievements").fetchall()]
    except Exception:
        return []


def unlock_achievement(achievement_id: str) -> bool:
    """Mark achievement as unlocked. Returns True if this is a new unlock."""
    today = date.today().isoformat()
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT unlocked FROM achievements WHERE achievement_id = ?",
                (achievement_id,),
            ).fetchone()
            if not row or row[0]:
                return False
            c.execute(
                "UPDATE achievements SET unlocked=1, unlocked_date=? WHERE achievement_id=?",
                (today, achievement_id),
            )
            return True
    except Exception:
        return False


def check_and_unlock_achievements(hunter: dict, skills: list,
                                   combo_today: bool = False) -> list:
    """Check all conditions; unlock new ones. Returns list of newly-unlocked IDs."""
    from game_logic import get_achievable_ids
    boss_count = get_boss_completions_count()
    achievable = get_achievable_ids(hunter, skills, combo_today, boss_count)
    return [aid for aid in achievable if unlock_achievement(aid)]


# ═══════════════════════════════════════════════════════════════════════════════
# Shop
# ═══════════════════════════════════════════════════════════════════════════════

SHOP_ITEMS = [
    {
        "item_id":   "streak_shield",
        "name":      "STREAK SHIELD",
        "desc":      "Protects your streak for one missed day",
        "cost":      150,
        "icon":      "🛡",
    },
    {
        "item_id":   "exp_boost",
        "name":      "EXP BOOST",
        "desc":      "Double EXP on all quests for today",
        "cost":      100,
        "icon":      "⚡",
    },
    {
        "item_id":   "gold_boost",
        "name":      "GOLD BOOST",
        "desc":      "Double Gold on all quests for today",
        "cost":      80,
        "icon":      "💰",
    },
    {
        "item_id":   "boss_ticket",
        "name":      "BOSS TICKET",
        "desc":      "Force-unlock this week's Boss Battle",
        "cost":      200,
        "icon":      "⚔",
    },
]


def _init_shop() -> None:
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS shop_inventory (
                item_id  TEXT PRIMARY KEY,
                quantity INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS active_boosts (
                boost_type   TEXT PRIMARY KEY,
                expires_date TEXT DEFAULT ''
            );
        """)
        for item in SHOP_ITEMS:
            c.execute(
                "INSERT OR IGNORE INTO shop_inventory (item_id, quantity) VALUES (?, 0)",
                (item["item_id"],),
            )


def get_shop_inventory() -> dict:
    """Returns {item_id: quantity}."""
    try:
        with _conn() as c:
            rows = c.execute("SELECT item_id, quantity FROM shop_inventory").fetchall()
            return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def purchase_item(item_id: str) -> dict:
    item = next((i for i in SHOP_ITEMS if i["item_id"] == item_id), None)
    if not item:
        return {"success": False, "message": "Item not found"}
    hunter = get_hunter()
    if hunter["gold"] < item["cost"]:
        return {"success": False,
                "message": f"Need {item['cost']} GOLD (have {hunter['gold']})"}
    update_hunter(gold=hunter["gold"] - item["cost"])
    with _conn() as c:
        c.execute(
            "UPDATE shop_inventory SET quantity = quantity + 1 WHERE item_id = ?",
            (item_id,),
        )
    return {"success": True, "message": f"Purchased {item['name']}", "gold_spent": item["cost"]}


def use_item(item_id: str) -> dict:
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT quantity FROM shop_inventory WHERE item_id = ?", (item_id,)
            ).fetchone()
            if not row or row[0] < 1:
                return {"success": False, "message": "Not in inventory"}
            c.execute(
                "UPDATE shop_inventory SET quantity = quantity - 1 WHERE item_id = ?",
                (item_id,),
            )
    except Exception as e:
        return {"success": False, "message": str(e)}

    today = date.today().isoformat()
    if item_id in ("exp_boost", "gold_boost"):
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO active_boosts (boost_type, expires_date) VALUES (?,?)",
                (item_id, today),
            )
    elif item_id == "streak_shield":
        set_setting("streak_shield", "1")
    elif item_id == "boss_ticket":
        unlock_boss()

    return {"success": True}


def get_active_boosts() -> dict:
    """Returns {boost_type: True} for active boosts expiring today."""
    today = date.today().isoformat()
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT boost_type FROM active_boosts WHERE expires_date = ?", (today,)
            ).fetchall()
            return {r[0]: True for r in rows}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# Boss Battles
# ═══════════════════════════════════════════════════════════════════════════════

def _init_boss() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS boss_battles (
                week           TEXT PRIMARY KEY,
                unlocked       INTEGER DEFAULT 0,
                completed      INTEGER DEFAULT 0,
                completed_date TEXT    DEFAULT '',
                exp_awarded    INTEGER DEFAULT 0
            )
        """)


def _current_week() -> str:
    cal = date.today().isocalendar()
    return f"{cal[0]}-W{cal[1]:02d}"


def get_boss_status() -> dict:
    week = _current_week()
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT * FROM boss_battles WHERE week = ?", (week,)
            ).fetchone()
            if not row:
                return {"week": week, "unlocked": False, "completed": False,
                        "exp_awarded": 0, "completed_date": ""}
            return dict(row)
    except Exception:
        return {"week": week, "unlocked": False, "completed": False,
                "exp_awarded": 0, "completed_date": ""}


def unlock_boss() -> None:
    week = _current_week()
    try:
        with _conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO boss_battles (week, unlocked) VALUES (?, 1)",
                (week,),
            )
            c.execute(
                "UPDATE boss_battles SET unlocked = 1 WHERE week = ?", (week,)
            )
    except Exception:
        pass


def complete_boss_battle() -> dict:
    from game_logic import apply_exp_gain, get_rank_info
    boss = get_boss_status()
    if not boss.get("unlocked"):
        return {"success": False, "message": "Boss not unlocked"}
    if boss.get("completed"):
        return {"success": False, "message": "Boss already completed this week"}

    exp_reward  = 200
    gold_reward = 100
    today = date.today().isoformat()
    week  = _current_week()

    with _conn() as c:
        c.execute(
            "UPDATE boss_battles SET completed=1, completed_date=?, exp_awarded=? WHERE week=?",
            (today, exp_reward, week),
        )

    h = get_hunter()
    old_level = h["level"]
    new_lvl, new_exp, new_nxt = apply_exp_gain(h["level"], h["current_exp"], exp_reward)
    _, new_title = get_rank_info(new_lvl)
    update_hunter(
        level=new_lvl, current_exp=new_exp, next_level_exp=new_nxt,
        gold=h["gold"] + gold_reward, title=new_title,
    )

    return {
        "success":      True,
        "exp_awarded":  exp_reward,
        "gold_awarded": gold_reward,
        "leveled":      new_lvl > old_level,
        "old_level":    old_level,
        "new_level":    new_lvl,
    }


def get_boss_completions_count() -> int:
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM boss_battles WHERE completed = 1"
            ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def check_boss_unlock() -> bool:
    """Unlock boss if hunter streak >= 5. Returns True if newly unlocked."""
    boss = get_boss_status()
    if boss.get("unlocked"):
        return False
    hunter = get_hunter()
    if hunter.get("streak", 0) >= 5:
        unlock_boss()
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Skill Goals
# ═══════════════════════════════════════════════════════════════════════════════

def _init_skill_goals() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS skill_goals (
                skill_name  TEXT PRIMARY KEY,
                target_rank TEXT DEFAULT '',
                deadline    TEXT DEFAULT ''
            )
        """)


def set_skill_goal(skill_name: str, target_rank: str, deadline: str = "") -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO skill_goals (skill_name, target_rank, deadline)"
            " VALUES (?, ?, ?)",
            (skill_name, target_rank, deadline),
        )


def clear_skill_goal(skill_name: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM skill_goals WHERE skill_name = ?", (skill_name,))


def get_skill_goals() -> dict:
    """Returns {skill_name: {target_rank, deadline}}."""
    try:
        with _conn() as c:
            rows = c.execute("SELECT * FROM skill_goals").fetchall()
            return {r["skill_name"]: {"target_rank": r["target_rank"],
                                      "deadline":    r["deadline"]}
                    for r in rows}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# Export
# ═══════════════════════════════════════════════════════════════════════════════

def export_progress_json(path: str) -> None:
    import json
    today      = date.today().isoformat()
    thirty_ago = (date.today() - timedelta(days=30)).isoformat()

    data = {
        "exported_at":    datetime.now().isoformat(),
        "hunter":         get_hunter(),
        "skills":         get_all_skills(),
        "skill_goals":    get_skill_goals(),
        "achievements":   [a for a in get_achievements() if a.get("unlocked")],
        "shop_inventory": get_shop_inventory(),
        "boss_battles":   get_boss_completions_count(),
        "recent_logs":    get_quest_logs_range(thirty_ago, today),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def export_progress_html(path: str) -> None:
    """Export a styled HTML progress report."""
    hunter        = get_hunter()
    skills        = get_all_skills()
    achievements  = [a for a in get_achievements() if a.get("unlocked")]
    today         = date.today().isoformat()
    thirty_ago    = (date.today() - timedelta(days=30)).isoformat()
    logs          = get_quest_logs_range(thirty_ago, today)
    done_days     = sum(1 for lg in logs if
                        lg.get("project_completed") and
                        lg.get("theory_completed")  and
                        lg.get("skill_completed"))

    from game_logic import get_rank_info, PRESTIGE_TITLES, get_prestige_title
    rank, title = get_rank_info(hunter["level"])
    prestige    = hunter.get("prestige_count", 0)
    ptitle      = get_prestige_title(prestige)

    skill_rows = "".join(
        f"<tr><td>{s['skill_name']}</td><td>{s['current_rank']}</td>"
        f"<td>{s['proficiency_points']} pts</td></tr>"
        for s in skills
    )
    ach_badges = "".join(
        f"<span class='badge'>{a['achievement_id'].upper()}</span>"
        for a in achievements
    )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Hunter Progress Report — {today}</title>
<style>
body{{font-family:monospace;background:#080d18;color:#deeeff;padding:32px;}}
h1{{color:#00d4ff;letter-spacing:4px;}}
h2{{color:#4a6a8a;letter-spacing:2px;font-size:13px;margin-top:24px;}}
table{{border-collapse:collapse;width:100%;margin:12px 0;}}
th{{color:#00d4ff;border-bottom:1px solid #0088bb;padding:6px 12px;text-align:left;}}
td{{padding:5px 12px;color:#deeeff;border-bottom:1px solid #152035;}}
.badge{{background:#0c1322;border:1px solid #0088bb;color:#00d4ff;
        padding:3px 8px;margin:3px;display:inline-block;font-size:11px;}}
.stat{{display:inline-block;margin:0 24px 12px 0;}}
.stat-val{{font-size:28px;font-weight:bold;color:#ffd700;}}
.stat-lbl{{font-size:10px;color:#4a6a8a;letter-spacing:2px;}}
</style></head>
<body>
<h1>■ HUNTER'S SYSTEM — PROGRESS REPORT ■</h1>
<p style="color:#4a6a8a">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<h2>HUNTER STATS</h2>
<div class='stat'><div class='stat-val'>LVL {hunter['level']}</div><div class='stat-lbl'>LEVEL</div></div>
<div class='stat'><div class='stat-val'>{rank}</div><div class='stat-lbl'>RANK</div></div>
<div class='stat'><div class='stat-val'>{hunter['streak']}</div><div class='stat-lbl'>STREAK</div></div>
<div class='stat'><div class='stat-val'>{hunter['gold']:,}</div><div class='stat-lbl'>GOLD</div></div>
<div class='stat'><div class='stat-val'>{done_days}/30</div><div class='stat-lbl'>30-DAY CLEARS</div></div>
{"<div class='stat'><div class='stat-val' style='color:#ff2244'>PRESTIGE " + str(prestige) + "</div><div class='stat-lbl'>" + ptitle + "</div></div>" if prestige > 0 else ""}

<h2>SKILL MATRIX</h2>
<table><tr><th>Skill</th><th>Rank</th><th>Points</th></tr>{skill_rows}</table>

<h2>ACHIEVEMENTS UNLOCKED ({len(achievements)})</h2>
<div>{ach_badges if ach_badges else '<span style="color:#1e3050">None yet</span>'}</div>

<p style="color:#1e3050;font-size:10px;margin-top:32px">Hunter's System Interface — DV Quest</p>
</body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ═══════════════════════════════════════════════════════════════════════════════
# Session Notes
# ═══════════════════════════════════════════════════════════════════════════════

def _init_session_notes() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS session_notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT    NOT NULL,
                quest_type TEXT    NOT NULL,
                note_text  TEXT    NOT NULL,
                timestamp  TEXT    NOT NULL
            )
        """)


def add_session_note(date_str: str, quest_type: str, note_text: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO session_notes (date, quest_type, note_text, timestamp) VALUES (?,?,?,?)",
                (date_str, quest_type, note_text.strip(), ts),
            )
    except Exception:
        pass


def get_session_notes(date_str: str) -> list:
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM session_notes WHERE date = ? ORDER BY id",
                (date_str,),
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def get_all_session_notes(limit: int = 100) -> list:
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM session_notes ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Side Quests
# ═══════════════════════════════════════════════════════════════════════════════

def _init_side_quests() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS side_quest_completions (
                quest_key TEXT PRIMARY KEY,
                date      TEXT NOT NULL,
                name      TEXT NOT NULL,
                exp_awarded  INTEGER DEFAULT 0,
                gold_awarded INTEGER DEFAULT 0
            )
        """)


def get_side_quest_completions(date_str: str) -> list:
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT quest_key FROM side_quest_completions WHERE date = ?", (date_str,)
            ).fetchall()
            return [r[0] for r in rows]
    except Exception:
        return []


def complete_side_quest(quest_key: str, date_str: str, name: str,
                        exp: int, gold: int) -> dict:
    from game_logic import apply_exp_gain, get_rank_info
    try:
        with _conn() as c:
            existing = c.execute(
                "SELECT 1 FROM side_quest_completions WHERE quest_key = ?", (quest_key,)
            ).fetchone()
            if existing:
                return {"success": False, "message": "Already completed"}
            c.execute(
                "INSERT INTO side_quest_completions (quest_key, date, name, exp_awarded, gold_awarded)"
                " VALUES (?,?,?,?,?)",
                (quest_key, date_str, name, exp, gold),
            )
    except Exception as e:
        return {"success": False, "message": str(e)}

    h = get_hunter()
    new_lvl, new_exp, new_nxt = apply_exp_gain(h["level"], h["current_exp"], exp)
    _, new_title = get_rank_info(new_lvl)
    update_hunter(level=new_lvl, current_exp=new_exp, next_level_exp=new_nxt,
                  gold=h["gold"] + gold, title=new_title)
    return {"success": True, "leveled": new_lvl > h["level"],
            "old_level": h["level"], "new_level": new_lvl}


# ═══════════════════════════════════════════════════════════════════════════════
# Pomodoro Sessions
# ═══════════════════════════════════════════════════════════════════════════════

def _init_pomodoro() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                started_at  TEXT NOT NULL,
                duration_mins INTEGER NOT NULL,
                completed   INTEGER DEFAULT 0
            )
        """)


def log_pomodoro(date_str: str, duration_mins: int, completed: bool) -> int:
    ts = datetime.now().isoformat(timespec="seconds")
    try:
        with _conn() as c:
            cur = c.execute(
                "INSERT INTO pomodoro_sessions (date, started_at, duration_mins, completed)"
                " VALUES (?,?,?,?)",
                (date_str, ts, duration_mins, 1 if completed else 0),
            )
            return cur.lastrowid
    except Exception:
        return -1


def get_pomodoro_count(date_str: str) -> int:
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM pomodoro_sessions WHERE date=? AND completed=1", (date_str,)
            ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def get_total_focus_hours() -> float:
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT SUM(duration_mins) FROM pomodoro_sessions WHERE completed=1"
            ).fetchone()
            return round((row[0] or 0) / 60, 1)
    except Exception:
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Study Resources
# ═══════════════════════════════════════════════════════════════════════════════

def _init_resources() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS study_resources (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                title      TEXT NOT NULL,
                url        TEXT DEFAULT '',
                note       TEXT DEFAULT ''
            )
        """)


def add_resource(skill_name: str, title: str, url: str = "", note: str = "") -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO study_resources (skill_name, title, url, note) VALUES (?,?,?,?)",
            (skill_name, title.strip(), url.strip(), note.strip()),
        )


def remove_resource(resource_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM study_resources WHERE id = ?", (resource_id,))


def get_resources(skill_name: str = None) -> list:
    try:
        with _conn() as c:
            if skill_name:
                rows = c.execute(
                    "SELECT * FROM study_resources WHERE skill_name = ? ORDER BY id",
                    (skill_name,),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM study_resources ORDER BY skill_name, id"
                ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Interview Concepts / Explain Out Loud
# ═══════════════════════════════════════════════════════════════════════════════

def _init_concepts() -> None:
    from concepts import INTERVIEW_CONCEPTS
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS concept_attempts (
                concept_id   INTEGER NOT NULL,
                date         TEXT NOT NULL,
                rating       TEXT DEFAULT '',
                time_taken   INTEGER DEFAULT 0,
                PRIMARY KEY (concept_id, date)
            )
        """)
        # Seed concepts table (just the IDs and metadata — full text is in concepts.py)
        c.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                concept_id INTEGER PRIMARY KEY,
                topic      TEXT,
                skill      TEXT,
                difficulty TEXT
            )
        """)
        for c_ in INTERVIEW_CONCEPTS:
            c.execute(
                "INSERT OR IGNORE INTO concepts (concept_id, topic, skill, difficulty) VALUES (?,?,?,?)",
                (c_["id"], c_["topic"], c_["skill"], c_["difficulty"]),
            )


def get_concept_attempts() -> dict:
    """Returns {concept_id: [attempt_dicts]}"""
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM concept_attempts ORDER BY date DESC"
            ).fetchall()
            result: dict = {}
            for r in rows:
                result.setdefault(r["concept_id"], []).append(dict(r))
            return result
    except Exception:
        return {}


def log_concept_attempt(concept_id: int, rating: str, time_taken: int) -> None:
    today = date.today().isoformat()
    try:
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO concept_attempts (concept_id, date, rating, time_taken)"
                " VALUES (?,?,?,?)",
                (concept_id, today, rating, time_taken),
            )
    except Exception:
        pass


def get_concept_stats() -> dict:
    """Returns {concept_id: {'attempts': N, 'last_date': ..., 'best_rating': ...}}"""
    try:
        with _conn() as c:
            rows = c.execute("SELECT * FROM concept_attempts").fetchall()
        stats: dict = {}
        _RATING_ORDER = {"good": 2, "partial": 1, "miss": 0, "": -1}
        for r in rows:
            cid = r["concept_id"]
            if cid not in stats:
                stats[cid] = {"attempts": 0, "last_date": "", "best_rating": ""}
            stats[cid]["attempts"] += 1
            if r["date"] > stats[cid]["last_date"]:
                stats[cid]["last_date"] = r["date"]
            if _RATING_ORDER.get(r["rating"], -1) > _RATING_ORDER.get(stats[cid]["best_rating"], -1):
                stats[cid]["best_rating"] = r["rating"]
        return stats
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# Prestige
# ═══════════════════════════════════════════════════════════════════════════════

def _init_prestige() -> None:
    """Add prestige_count column to hunter_stats if missing."""
    with _conn() as c:
        existing = {r[1] for r in c.execute("PRAGMA table_info(hunter_stats)").fetchall()}
        if "prestige_count" not in existing:
            c.execute("ALTER TABLE hunter_stats ADD COLUMN prestige_count INTEGER DEFAULT 0")
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS prestige_log (
                prestige_num  INTEGER PRIMARY KEY,
                prestige_date TEXT NOT NULL,
                level_reached INTEGER NOT NULL,
                gold_kept     INTEGER NOT NULL
            )
        """)


def can_prestige() -> bool:
    hunter = get_hunter()
    return hunter.get("level", 0) >= 60


def do_prestige() -> dict:
    from game_logic import get_prestige_title
    if not can_prestige():
        return {"success": False, "message": "Must reach Level 60 (S-Rank) to prestige"}

    hunter  = get_hunter()
    old_lvl = hunter["level"]
    old_gold = hunter.get("gold", 0)
    kept_gold = old_gold // 2   # keep half the gold on prestige
    prestige_num = (hunter.get("prestige_count", 0) or 0) + 1

    with _conn() as c:
        c.execute(
            "INSERT INTO prestige_log (prestige_num, prestige_date, level_reached, gold_kept)"
            " VALUES (?,?,?,?)",
            (prestige_num, date.today().isoformat(), old_lvl, kept_gold),
        )

    update_hunter(
        level=1, current_exp=0, next_level_exp=100,
        gold=kept_gold,
        title=get_prestige_title(prestige_num),
        prestige_count=prestige_num,
    )
    return {
        "success":      True,
        "prestige_num": prestige_num,
        "old_level":    old_lvl,
        "gold_kept":    kept_gold,
        "title":        get_prestige_title(prestige_num),
    }


def get_prestige_log() -> list:
    try:
        with _conn() as c:
            rows = c.execute("SELECT * FROM prestige_log ORDER BY prestige_num").fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Last-practiced tracking (for spaced repetition)
# ═══════════════════════════════════════════════════════════════════════════════

def get_skill_last_practiced() -> dict:
    """Returns {skill_name: last_date_str} from quest_log skill completions."""
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT skill_name, MAX(date) as last_date FROM quest_log "
                "WHERE skill_completed = 1 AND skill_name IS NOT NULL AND skill_name != '' "
                "GROUP BY skill_name"
            ).fetchall()
            return {r["skill_name"]: r["last_date"] for r in rows}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# Backup / Restore
# ═══════════════════════════════════════════════════════════════════════════════

def backup_db(dest_path: str) -> None:
    import shutil
    shutil.copy2(DB_PATH, dest_path)


def restore_db(src_path: str) -> None:
    import shutil
    shutil.copy2(src_path, DB_PATH)
