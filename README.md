# Planner

This is **APEX Program** (using **UV python package manager**).
**Your Ultimate Planning and Daily System** to use for your life.
Inspired by [Solo Leveling](https://www.imdb.com/title/tt21209876/)

![Planner](./Planner.avif)

## Features

- 🛡️ The Gate (Dashboard): A unified command center to track your daily timeline, biometrics, and active missions at a glance.

- ⚔️ Quest Board: Gamify your life by treating Habits and Routines as Ranked Quests (E-Rank to S-Rank) that award XP based on difficulty and fear.

- 🏰 Conquest System: Turn long-term goals into multi-stage Dungeons. Progress from "Scouting" to the final "Boss Fight" to clear major life milestones.

- 🧠 Dynamic Stats: Watch your real-life attributes (Physique, Intellect, Charisma, Discipline, Psyche) level up as you complete relevant tasks.

- 🎒 Inventory & Wealth: A dedicated system to track your assets, net worth ("Gold"), and consumables, separating your finances from your equipment.

- 📚 The Library: An active reading tracker that logs pages read and time spent, directly feeding into your Intellect stat.

- ❤️ Biometric Tracking: Monitor your Energy, Mood, and Sleep patterns to ensure your "Player Character" stays in peak condition.

- 📜 Hunter’s Journal: A daily reflection system ("Wins" & "Lessons") that converts your daily experiences into Wisdom XP.

## 🛠 Tech Stack

- **Backend:** Python, Django 5.2, Django REST Framework
- **BacFrontend:** Django Templates, Bootstrap 5, HTML5, CSS3, Vanilla JavaScript
- **Database:** PostgreSQL
- **DevOps & Infrastructure:** Docker, Docker Compose
- **Tooling:** UV (Python Package Manager), Bash/Shell Scripts

## Setup

To run project locally, in production or using Docker you need to setup environment variables first. Rename the `.env.example` to `.env` and fill the required values.

You can also use this command in linux for ease of use to have `.env` file in `/backend` directory as well:

```bash
ln -s ../.env backend/.env
```

### Backend Setup (Django)

1. Install dependencies:
First install [uv package manager](https://docs.astral.sh/uv/getting-started/installation/) (feel free to read [uv documents](https://docs.astral.sh/uv/getting-started/))

   ```bash
   pip install uv
   ```

2. install packages:

   ```bash
   cd backend
   uv sync
   ```

3. Run migrations:

   ```bash
   uv run manage.py makemigrations
   uv run manage.py migrate
   ```

4. Start the backend server:

   ```bash
   uv run manage.py runserver
   ```

### Running with Docker

- Just build and start all services **(recommended)**:
  
   ```bash
   docker compose up --build
   ```

## Project Architecture

This project follows a Domain-Driven modular structure.
Models and Admin configuration are split into packages.

```bash
APEX Program/
├── backend/
│   ├── apps/                         # GAMEPLAY DOMAINS
│   │   ├── profiles/                 # App 1: Character Sheet
│   │   │   ├── models/               # (Split: Profile, Stats, Titles)
│   │   │   ├── admin/                # (Split: Modular Admin configs)
│   │   │   ├── services.py           # XP & Leveling Logic
│   │   │   └── signals.py            # Level Up Triggers
│   │   │
│   │   ├── gate/                     # App 2: Dashboard & Time
│   │   │   ├── models/               # (Split: DailyEntry, Journal)
│   │   │   └── utils.py              # Date conversion (Gregorian <-> Jalali)
│   │   │
│   │   ├── quests/                   # App 3: Action Engine
│   │   │   ├── models/               # (Split: Task, Habit, Logs)
│   │   │   └── services.py           # Rank Calculation Algorithm
│   │   │
│   │   ├── inventory/                # App 4: Wealth & Assets
│   │   │   ├── models/               # (Split: Wallet, Items, Finance)
│   │   │   └── admin/
│   │   │
│   │   ├── library/                  # App 5: Knowledge System
│   │   │   ├── models/               # (Split: Book, ReadingSession)
│   │   │   ├── services.py           # Reading Stats Logic
│   │   │   └── signals.py            # INT Stat Trigger
│   │   │
│   │   └── conquests/                # App 6: Story Mode
│   │       ├── models/               # (Split: Dungeon, Arc, RedGate)
│   │       └── services.py           # Boss Mode Logic
│   │
│   ├── auths/                        # IDENTITY
│   │   └── user/                     # Custom User Model
│   │
│   ├── core/                         # CONFIGURATION
│   │   ├── settings/                 # (base.py, dev.py, prod.py)
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── static/                       # ASSETS (css, js, vendor)
│   ├── templates/                    # HTML (base.html, app folders)
│   ├── entrypoint.sh
│   ├── manage.py
│   └── pyproject.toml
│
├── dockerfiles/                      # Docker Configs
├── node_modules/                     # Frontend Dependencies
├── compose.yaml
├── package.json
└── update_vendor.py                  # Script: Copy npm -> static
```

## Contributing

Contributions are always welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/).
