# ⚔ Hunter's System Interface

A gamified desktop app that turns daily skill-building and interview prep into an RPG. Built with **Python + PySide6**, themed after *Solo Leveling*'s "System" — complete daily quests, level up, rank up, unlock achievements, and grind your way to S-Rank.

Originally built for Design Verification (DV/VLSI) engineering interview prep, but **fully reskinnable for any career** — see [Adapt This For Your Own Career](#-adapt-this-for-your-own-career) below.

---

## ✨ Features

**Core loop**
- Daily quests (Project / Theory / Skill) with EXP, Gold, and combo bonuses
- Leveling + rank system (E-Rank → S-Rank) with animated rank-up overlay
- Streak tracking with a "penalty zone" lockout if you miss a day
- Custom task editor — define your own quests beyond the defaults

**Progression systems**
- Skill proficiency tracking with an interactive skill-tree visualization
- Skill goals with deadlines
- Prestige system (reset at Level 60 for a permanent title)
- Achievement/badge system (20 unlockable achievements)
- Gold shop (streak shields, EXP/Gold boosts, boss tickets)
- Weekly Boss Battles (unlock at a 5-day streak)
- Daily side quests (deterministic per-day pool)

**Study tools**
- **Explain It Out Loud** — interview-style concept practice: read a question, explain it out loud, reveal the model answer, rate yourself, and track attempt history per concept
- Pomodoro focus timer with session logging
- Study resources panel (save links/notes per skill)
- Spaced-repetition-friendly "last practiced" tracking

**Visibility & polish**
- Calendar heatmap, stats dashboard, and quest journal
- Exportable JSON / HTML progress reports
- Database backup & restore
- System tray support — minimizes to tray, daily reminder notifications, runs fully in the background
- Two themes (Cyan / Crimson), animated particle background, sound effects

---

## 🚀 Getting Started

```bash
git clone https://github.com/<your-username>/hunters-system.git
cd hunters-system
pip install -r requirements.txt
python main.py
```

**To run silently in the background** (no console window, survives closing your terminal/IDE):
double-click `start_app.vbs` instead of running `main.py` directly.

### Requirements
- Python 3.10+
- PySide6
- pygame (for sound effects — optional, app runs fine without audio files)

---

## 🎯 Adapt This For Your Own Career

The quest categories, skills, and the 25-question "Explain It Out Loud" bank are written for DV/VLSI engineering — but the entire app is data-driven. You can retheme it for **any** field (software engineering, data science, product management, finance, law, nursing, etc.) by regenerating three files.

Copy this prompt into Claude, ChatGPT, or any capable LLM:

> I'm using a gamified study/interview-prep app built in Python. It tracks daily quests, EXP, skill ranks, and has an "Explain It Out Loud" concept-practice panel where I read a question, explain the answer out loud, then reveal a model answer to compare against. I want to adapt its content for my own career field instead of its original domain.
>
> Please generate three things, in the exact structure below:
>
> **1. A SKILLS list** — 6 to 9 short core skill/topic categories for my field, as a flat Python list of strings.
>
> **2. An INTERVIEW_CONCEPTS list** — 20 to 25 interview question/answer pairs for my field, each formatted as:
> ```python
> {
>     "id": <int>, "topic": "<topic name>", "skill": "<must match one of my SKILLS>", "difficulty": "<E, D, C, B, A, or S — easiest to hardest>",
>     "question": "<a real interview question>",
>     "answer": "<a thorough model answer, written as if explaining out loud, 3-6 sentences>",
> },
> ```
>
> **3. A SIDE_QUEST_POOL** — 25 to 30 small daily practice tasks for my field, each formatted as:
> ```python
> {"name": "<short task description>", "category": "PROJECT, THEORY, or SKILL", "exp": <15-30>, "gold": <7-15>},
> ```
>
> My career field is: **[FILL IN]**
> My target role / seniority is: **[FILL IN, e.g. "junior backend developer" or "senior product manager"]**
> My specific interview focus areas are: **[FILL IN, e.g. "system design, SQL, behavioral questions" or "case studies, market sizing, metrics"]**

Then drop the results in:
- `SKILLS` → `database.py` (top of file)
- `INTERVIEW_CONCEPTS` → `concepts.py` (replace the list)
- `SIDE_QUEST_POOL` → `game_logic.py` (replace the list)

Delete `hunter.db` (or run the app once — it self-creates) and you're fully retheme'd.

---

## 🛠 Tech Stack

- **PySide6** (Qt for Python) — UI, custom `QPainter` graphics (calendar heatmap, skill tree, rank-up scan-line effect, particle background)
- **SQLite** — single-file local database, no server required
- **pygame.mixer** — optional sound effects / background music
- Zero cloud dependencies — everything runs and stores data locally

---

## 📁 Project Structure

```
main.py                 entry point
database.py             all SQLite access
game_logic.py            pure game-rule functions (EXP curves, ranks, achievements)
concepts.py              interview question bank
audio_engine.py          sound effect / music playback
date_helper.py           date utilities (dev-mode date simulation)
ui/
  main_window.py         top-level window, tab navigation, game loop wiring
  theme.py                color palette + QSS stylesheets
  widgets/                reusable widgets (quest cards, exp bar, pomodoro timer, ...)
  overlays/               full-screen overlays (level-up, rank-up, prestige, penalty zone)
  panels/                 tab content (achievements, shop, stats, explain, settings, ...)
```

---

## License

Personal project — use, fork, and reskin freely.
