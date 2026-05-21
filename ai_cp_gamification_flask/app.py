from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "gamification.db"

app = Flask(__name__)

LEVELS = [
    {"level": 1, "title": "Beginner", "min": 0, "max": 249},
    {"level": 2, "title": "CP Assistant", "min": 250, "max": 499},
    {"level": 3, "title": "Proposal Specialist", "min": 500, "max": 899},
    {"level": 4, "title": "Sales Contributor", "min": 900, "max": 1249},
    {"level": 5, "title": "Proposal Pro", "min": 1250, "max": 1749},
    {"level": 6, "title": "Deal Closer", "min": 1750, "max": 2499},
    {"level": 7, "title": "CP Master", "min": 2500, "max": 10**12},
]

ACHIEVEMENTS = [
    {
        "code": "first_proposal",
        "name": "First Proposal",
        "description": "Создать первое коммерческое предложение",
        "icon": "📄",
    },
    {
        "code": "proposal_pro",
        "name": "Proposal Pro",
        "description": "Набрать 1250 очков",
        "icon": "🏅",
    },
    {
        "code": "deal_closer",
        "name": "Deal Closer",
        "description": "Получить 5 одобренных КП",
        "icon": "🏆",
    },
    {
        "code": "quality_expert",
        "name": "Quality Expert",
        "description": "Получить бонус +150 или выше",
        "icon": "⭐",
    },
    {
        "code": "elite_performer",
        "name": "Elite Performer",
        "description": "Получить бонус +200",
        "icon": "💎",
    },
    {
        "code": "streak_master",
        "name": "Streak Master",
        "description": "Создавать КП 5 дней подряд",
        "icon": "🔥",
    },
]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def get_level(points: int) -> dict[str, Any]:
    for level in LEVELS:
        if level["min"] <= points <= level["max"]:
            return level
    return LEVELS[0]


def get_level_progress(points: int) -> int:
    level = get_level(points)
    if level["max"] >= 10**12:
        return 100
    span = level["max"] - level["min"] + 1
    completed = points - level["min"]
    return max(0, min(100, round(completed / span * 100)))


def execute_schema() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                total_points INTEGER NOT NULL DEFAULT 0,
                generated_count INTEGER NOT NULL DEFAULT 0,
                approved_count INTEGER NOT NULL DEFAULT 0,
                best_bonus INTEGER NOT NULL DEFAULT 0,
                current_streak INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                ai_confidence INTEGER NOT NULL DEFAULT 90,
                generated_text TEXT NOT NULL,
                effectiveness_bonus INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewed_by INTEGER,
                FOREIGN KEY(author_id) REFERENCES users(id),
                FOREIGN KEY(reviewed_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                proposal_id INTEGER,
                action_type TEXT NOT NULL,
                points INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(proposal_id) REFERENCES proposals(id)
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TEXT NOT NULL,
                UNIQUE(user_id, achievement_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(achievement_id) REFERENCES achievements(id)
            );
            """
        )


def seed_data() -> None:
    with get_db() as conn:
        users_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if users_count == 0:
            conn.execute(
                """
                INSERT INTO users
                (name, role, total_points, generated_count, approved_count, best_bonus, current_streak, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("A. Ivanov", "employee", 1250, 4, 2, 150, 5, now_iso()),
            )
            conn.execute(
                """
                INSERT INTO users
                (name, role, total_points, generated_count, approved_count, best_bonus, current_streak, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Admin", "admin", 0, 0, 0, 0, 0, now_iso()),
            )
            conn.execute(
                """
                INSERT INTO users
                (name, role, total_points, generated_count, approved_count, best_bonus, current_streak, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("M. Lee", "employee", 980, 3, 1, 100, 2, now_iso()),
            )
            conn.execute(
                """
                INSERT INTO users
                (name, role, total_points, generated_count, approved_count, best_bonus, current_streak, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("J. Doe", "employee", 820, 2, 1, 50, 1, now_iso()),
            )

        for achievement in ACHIEVEMENTS:
            conn.execute(
                """
                INSERT OR IGNORE INTO achievements (code, name, description, icon)
                VALUES (?, ?, ?, ?)
                """,
                (
                    achievement["code"],
                    achievement["name"],
                    achievement["description"],
                    achievement["icon"],
                ),
            )

        proposals_count = conn.execute("SELECT COUNT(*) AS c FROM proposals").fetchone()["c"]
        if proposals_count == 0:
            proposals = [
                (
                    "Infrastructure Optimization",
                    "Tech Solutions Corp",
                    1,
                    "pending",
                    94,
                    "The proposed technical architecture leverages a multi-region cloud deployment strategy focused on 99.99% availability and reduced operating costs.",
                ),
                (
                    "Internal UX Workshop",
                    "Global Dynamics Ltd",
                    3,
                    "pending",
                    88,
                    "Bi-weekly collaborative sessions for cross-departmental design alignment and interface consistency checks.",
                ),
                (
                    "Security Audit Refresh",
                    "Stellar Innovations",
                    4,
                    "pending",
                    91,
                    "Quarterly deep-dive into third-party dependencies to maintain compliance and reduce risk exposure.",
                ),
                (
                    "Frontend Refactor",
                    "Enterprise Sales Team",
                    1,
                    "approved",
                    90,
                    "Refactor proposal focused on maintainability, component reuse, and faster delivery cycles.",
                ),
            ]
            for title, company, author_id, status, confidence, text in proposals:
                reviewed_at = now_iso() if status == "approved" else None
                reviewed_by = 2 if status == "approved" else None
                conn.execute(
                    """
                    INSERT INTO proposals
                    (title, company, author_id, status, ai_confidence, generated_text,
                     effectiveness_bonus, created_at, reviewed_at, reviewed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        title,
                        company,
                        author_id,
                        status,
                        confidence,
                        text,
                        50 if status == "approved" else 0,
                        now_iso(),
                        reviewed_at,
                        reviewed_by,
                    ),
                )

        transactions_count = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
        if transactions_count == 0:
            conn.executemany(
                """
                INSERT INTO transactions (user_id, proposal_id, action_type, points, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (1, 4, "proposal_approved", 150, "Initial approved proposal", now_iso()),
                    (1, 1, "proposal_generated", 50, "Generated CP #1", now_iso()),
                    (3, 2, "proposal_generated", 50, "Generated CP #2", now_iso()),
                ],
            )


def init_app_data() -> None:
    execute_schema()
    seed_data()
    with get_db() as conn:
        for user in conn.execute("SELECT id FROM users WHERE role = 'employee'").fetchall():
            unlock_achievements(conn, user["id"])


def get_primary_employee(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute("SELECT * FROM users WHERE role = 'employee' ORDER BY id LIMIT 1").fetchone()


def get_admin(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute("SELECT * FROM users WHERE role = 'admin' ORDER BY id LIMIT 1").fetchone()


def add_transaction(
    conn: sqlite3.Connection,
    user_id: int,
    proposal_id: int | None,
    action_type: str,
    points: int,
    comment: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO transactions (user_id, proposal_id, action_type, points, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, proposal_id, action_type, points, comment, now_iso()),
    )


def unlock_achievements(conn: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return []

    checks = {
        "first_proposal": user["generated_count"] >= 1,
        "proposal_pro": user["total_points"] >= 1250,
        "deal_closer": user["approved_count"] >= 5,
        "quality_expert": user["best_bonus"] >= 150,
        "elite_performer": user["best_bonus"] >= 200,
        "streak_master": user["current_streak"] >= 5,
    }

    unlocked: list[dict[str, Any]] = []
    for code, passed in checks.items():
        if not passed:
            continue
        achievement = conn.execute("SELECT * FROM achievements WHERE code = ?", (code,)).fetchone()
        if not achievement:
            continue
        before = conn.total_changes
        conn.execute(
            """
            INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, unlocked_at)
            VALUES (?, ?, ?)
            """,
            (user_id, achievement["id"], now_iso()),
        )
        if conn.total_changes > before:
            unlocked.append(dict(achievement))
    return unlocked


def get_state() -> dict[str, Any]:
    with get_db() as conn:
        employee = get_primary_employee(conn)
        admin = get_admin(conn)
        level = get_level(employee["total_points"])
        proposals = [
            dict(row)
            for row in conn.execute(
                """
                SELECT p.*, u.name AS author_name
                FROM proposals p
                JOIN users u ON u.id = p.author_id
                ORDER BY p.id DESC
                """
            ).fetchall()
        ]
        transactions = [
            dict(row)
            for row in conn.execute(
                """
                SELECT t.*, u.name AS user_name, p.title AS proposal_title
                FROM transactions t
                JOIN users u ON u.id = t.user_id
                LEFT JOIN proposals p ON p.id = t.proposal_id
                ORDER BY t.id DESC
                LIMIT 10
                """
            ).fetchall()
        ]
        achievements = [
            dict(row)
            for row in conn.execute(
                """
                SELECT a.*, ua.unlocked_at,
                       CASE WHEN ua.id IS NULL THEN 0 ELSE 1 END AS unlocked
                FROM achievements a
                LEFT JOIN user_achievements ua
                  ON ua.achievement_id = a.id AND ua.user_id = ?
                ORDER BY a.id
                """,
                (employee["id"],),
            ).fetchall()
        ]
        leaderboard = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, name, total_points, generated_count, approved_count
                FROM users
                WHERE role = 'employee'
                ORDER BY total_points DESC
                """
            ).fetchall()
        ]

        return {
            "employee": dict(employee),
            "admin": dict(admin),
            "level": level,
            "level_progress": get_level_progress(employee["total_points"]),
            "proposals": proposals,
            "transactions": transactions,
            "achievements": achievements,
            "leaderboard": leaderboard,
        }


@app.route("/")
def index():
    return render_template("employee.html", state=get_state(), active="employee")


@app.route("/admin")
def admin_page():
    return render_template("admin.html", state=get_state(), active="admin")


@app.route("/achievements")
def achievements_page():
    return render_template("achievements.html", state=get_state(), active="achievements")


@app.route("/leaderboard")
def leaderboard_page():
    return render_template("leaderboard.html", state=get_state(), active="leaderboard")


@app.route("/api/state")
def api_state():
    return jsonify(get_state())


@app.post("/api/proposals/generate")
def api_generate_proposal():
    data = request.get_json(silent=True) or {}
    title = data.get("title") or "AI Commercial Proposal"
    company = data.get("company") or "New Enterprise Client"
    generated_text = data.get("generated_text") or (
        "AI generated a commercial proposal with optimized terminology, "
        "pricing structure, business value, and implementation timeline."
    )

    with get_db() as conn:
        employee = get_primary_employee(conn)
        cursor = conn.execute(
            """
            INSERT INTO proposals
            (title, company, author_id, status, ai_confidence, generated_text, effectiveness_bonus, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?, 0, ?)
            """,
            (title, company, employee["id"], 92, generated_text, now_iso()),
        )
        proposal_id = int(cursor.lastrowid)
        conn.execute(
            """
            UPDATE users
            SET total_points = total_points + 50,
                generated_count = generated_count + 1,
                current_streak = CASE WHEN current_streak < 5 THEN current_streak + 1 ELSE current_streak END
            WHERE id = ?
            """,
            (employee["id"],),
        )
        add_transaction(
            conn,
            employee["id"],
            proposal_id,
            "proposal_generated",
            50,
            "Начисление за генерацию КП",
        )
        unlocked = unlock_achievements(conn, employee["id"])

    return jsonify({"ok": True, "points_awarded": 50, "proposal_id": proposal_id, "unlocked": unlocked})


@app.post("/api/proposals/<int:proposal_id>/approve")
def api_approve_proposal(proposal_id: int):
    data = request.get_json(silent=True) or {}
    bonus = int(data.get("bonus", 100))
    if bonus not in {50, 100, 150, 200}:
        return jsonify({"ok": False, "error": "Bonus must be one of: 50, 100, 150, 200"}), 400

    with get_db() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        if not proposal:
            return jsonify({"ok": False, "error": "Proposal not found"}), 404
        if proposal["status"] != "pending":
            return jsonify({"ok": False, "error": "Proposal is not pending"}), 409

        admin = get_admin(conn)
        total = 100 + bonus
        conn.execute(
            """
            UPDATE proposals
            SET status = 'approved', effectiveness_bonus = ?, reviewed_at = ?, reviewed_by = ?
            WHERE id = ?
            """,
            (bonus, now_iso(), admin["id"], proposal_id),
        )
        conn.execute(
            """
            UPDATE users
            SET total_points = total_points + ?,
                approved_count = approved_count + 1,
                best_bonus = CASE WHEN best_bonus < ? THEN ? ELSE best_bonus END
            WHERE id = ?
            """,
            (total, bonus, bonus, proposal["author_id"]),
        )
        add_transaction(
            conn,
            proposal["author_id"],
            proposal_id,
            "proposal_approved",
            total,
            f"Одобрение КП: +100 base и +{bonus} bonus",
        )
        unlocked = unlock_achievements(conn, proposal["author_id"])

    return jsonify({"ok": True, "points_awarded": total, "unlocked": unlocked})


@app.post("/api/proposals/<int:proposal_id>/reject")
def api_reject_proposal(proposal_id: int):
    with get_db() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        if not proposal:
            return jsonify({"ok": False, "error": "Proposal not found"}), 404
        if proposal["status"] != "pending":
            return jsonify({"ok": False, "error": "Proposal is not pending"}), 409
        admin = get_admin(conn)
        conn.execute(
            """
            UPDATE proposals
            SET status = 'rejected', reviewed_at = ?, reviewed_by = ?
            WHERE id = ?
            """,
            (now_iso(), admin["id"], proposal_id),
        )
        add_transaction(
            conn,
            proposal["author_id"],
            proposal_id,
            "proposal_rejected",
            0,
            "КП отклонено администратором",
        )

    return jsonify({"ok": True})


@app.post("/api/reset-demo")
def api_reset_demo():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_app_data()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_app_data()
    app.run(debug=True)
else:
    init_app_data()
