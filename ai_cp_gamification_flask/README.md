# AI CP Gamification Subsystem

Мини-проект подсистемы геймификации для AI-системы генерации коммерческих предложений.

## Стек

- Backend: Python + Flask
- Frontend: HTML-шаблоны Jinja, CSS, JavaScript
- Storage: SQLite

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

После запуска откройте:

- Employee Dashboard: http://127.0.0.1:5000/
- Admin Dashboard: http://127.0.0.1:5000/admin
- Achievements: http://127.0.0.1:5000/achievements
- Leaderboard: http://127.0.0.1:5000/leaderboard

## Основная логика

- Генерация КП: +50 очков.
- Одобрение КП: +100 базовых очков + бонус администратора.
- Бонусы: +50, +100, +150, +200.
- Достижения открываются автоматически.
- Уровень пользователя пересчитывается на основе total_points.

## API

- `GET /api/state` — состояние системы.
- `POST /api/proposals/generate` — создать КП и начислить +50.
- `POST /api/proposals/<id>/approve` — одобрить КП и начислить очки.
- `POST /api/proposals/<id>/reject` — отклонить КП.
- `POST /api/reset-demo` — сбросить демо-базу.
