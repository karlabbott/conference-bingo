# Conference Bingo 🎯

An interactive bingo game for conference talks — attendees each get a randomized 5×5 card with talk-themed squares and tap them as events happen during the presentation. First to complete a row, column, or diagonal gets announced to everyone with confetti!

Built for **"Microsoft for Red Hat Teams: Modern RHEL Operations on Azure with Copilot"**.

![Bingo](https://img.shields.io/badge/game-Conference_Bingo-538d4e?style=for-the-badge)

## Features

- **🎯 Randomized Cards** — Each attendee gets a unique 5×5 card drawn from 48 possible squares
- **📱 Mobile-first** — Designed for phones at a conference; tap squares as things happen
- **🏆 Live Winners Feed** — When someone gets bingo, all players see the announcement
- **🎉 Confetti Celebration** — Confetti burst when you claim bingo
- **⭐ Free Center** — Classic bingo free space in the middle
- **🔄 Admin Controls** — Add/remove squares, reset the game between sessions, view stats
- **🍪 12-Hour Sessions** — Cookie-based player persistence (survives WiFi changes)
- **🎭 Honor System** — Players self-mark squares, keeping it fun and low-friction

## How It Works

1. Attendee visits the URL on their phone
2. Enters their name → gets a randomized bingo card
3. During the talk, they tap squares as events occur ("Copilot writes a bash script", "SELinux is mentioned", etc.)
4. When they complete a row, column, or diagonal → the BINGO button activates
5. They tap BINGO → confetti! Their name appears on everyone's winner ticker

## Architecture

```
Browser → Nginx (SSL/443) → Gunicorn (Flask :5000) → PostgreSQL (:5432)
```

## Quick Start (Development)

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### 1. Set up PostgreSQL

```bash
sudo -u postgres psql -c "CREATE ROLE bingo WITH LOGIN PASSWORD 'bingo';"
sudo -u postgres psql -c "CREATE DATABASE conference_bingo OWNER bingo;"
```

### 2. Set up Python environment

```bash
git clone https://github.com/karlabbott/conference-bingo.git
cd conference-bingo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Initialize database and seed squares

```bash
python -c "from app.db import init_db; init_db()"
python -m app.seed
```

### 4. Run the development server

```bash
flask --app wsgi:app run --debug
```

Open http://localhost:5000 in your browser.

## Production Deployment

### 1. Configure

```bash
cp config.env.example config.env
nano config.env
```

Edit these values:
- `BINGO_HOSTNAME` — Your domain name
- `SECRET_KEY` — A random secret key
- `DB_PASSWORD` — A strong database password
- `ADMIN_PASSWORD` — Password for the admin panel

### 2. Run setup

Follow the same deployment pattern as the standard Flask + Gunicorn + Nginx stack.

## Admin Panel

Visit `/admin` and enter the admin password to:
- **View stats** — Active players, cards dealt, winners
- **Manage squares** — Add, remove, or edit bingo square text
- **Reset game** — Clear all cards and marks (players get new cards on next visit)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Bingo card page |
| GET | `/admin` | Admin panel |
| POST | `/api/register` | Register player name |
| GET | `/api/me` | Get current player info |
| GET | `/api/card` | Get or generate bingo card |
| POST | `/api/mark` | Mark/unmark a square |
| POST | `/api/bingo` | Claim bingo (server validates) |
| GET | `/api/winners` | Live winners feed |
| GET | `/api/admin/stats` | Game statistics |
| POST | `/api/admin/squares` | Add a square |
| DELETE | `/api/admin/squares/:id` | Remove a square |
| POST | `/api/admin/reset` | Reset game |

## Default Bingo Squares (48)

Themed to RHEL + Azure + Copilot operations:

> "Copilot writes a bash script" · "A systemctl command appears" · "Someone mentions RHEL 9" · "A live demo works first try" · "Azure CLI is used" · "SELinux is mentioned" · "sudo is used" · "The audience laughs" · and 40 more...

Customize via the admin panel before your talk!

## License

MIT
