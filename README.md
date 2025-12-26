# ⚔️ The APEX Program Documentation

> The weak always lose...
Because it's only the strong who survive!

This is **[The APEX Program](https://github.com/haadijafari/APEX_Program)!**
**Your Ultimate Planning and Daily System** to use for your life.

![Apex Program](./docs/apex.png)

Welcome to the official documentation. [APEX Program](https://github.com/haadijafari/APEX_Program) is a gamified life-management system inspired by the [Solo Leveling](https://www.imdb.com/title/tt21209876/)'s "System". The goal of this project is to manage every aspect of your life you want to improve (in An RPG style experience).

## ✨ Features

- **Smart Task Prioritization:** Automatically ranks daily to-dos using a "Complexity Score" that weighs duration, effort, and psychological resistance (Fear Factor).

- **Habit & Routine Builder:** Tracks consistency through streaks and groups related habits into executable sequences (e.g., Morning Routine).

- **Goal & Project Execution:** Manages complex projects ("Dungeons") with Kanban boards, strictly enforced deadlines, and emergency timers to prevent procrastination.

- **Long-Term Vision Planning:** Structures life goals into 4 distinct horizons: 25-year Visions, 10-year Questlines, Monthly Arcs, and Daily Tasks.

- **Seasonal Focus Themes:** Organizes time into "Arcs" (e.g., "The Awakening Arc"), allowing you to filter current objectives based on your life's current chapter or season.

- **Failure Analysis & Reflection:** Includes a "Strategic Withdrawal" protocol that prompts you to journal reasons for abandoning goals, turning failures into "Wisdom" data rather than just loss.

- **Learning Management System (LMS):** A dedicated "Library" to track reading lists, log study sessions, and manage progress on books or online courses.

- **Financial Portfolio:** Monitors liquid assets (Gold), income sources, and savings goals alongside a ledger for major expenditures.

- **Inventory & Consumables:** Tracks possession of physical assets (e.g., tech gear) and manages recurring consumables like supplements with status indicators (e.g., "Low", "Empty").

- **Milestone & Legacy Tracking:** Automates "Feats of Strength" badges for aggregate data (e.g., "10,000 Pages Read") and awards Titles to validate identity shifts.

## 🛠️ Tech Stack

- ***Programming Language***
  - **Python 3.10+**
  - **UV** – ultra-fast Python package manager and virtual environment replacement
- ***Backend***
  - **Django 5.2**
  - **Django REST Framework** – API layer for data synchronization across devices
- ***Database***
  - **PostgreSQL**
- ***Frontend***
  - **Django Templates**
  - **Bootstrap 5.3** (Dark Mode)
  - **HTML5, CSS3**
- ***Client-Side Scripting***
  - **Vanilla JavaScript (ES6)**
- ***JavaScript Tooling***
  - **Node.js**
  - **npm** – package manager for frontend dependencies and build tools
- ***DevOps & Environment***
  - **Docker & Docker Compose** – optional containerized setup for desktop environments
  - **Temux** - run the full Django backend natively on Android (no hosting, no domain)
- ***Tooling & Automation***
  - **UV** - dependency management & project execution
  - **Bash/Shell Scripts** - environment setup and automation

## 🚀 Quick Start

The APEX Program is designed to run on a local server, specifically optimized for Android Termux and Localhost.

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

## 📂 Documentation

You can visit `docs/` directory which contains the records for the system's logic, architecture, and data design.

01. [Scenario & Game Mechanics](./docs/Senario.md)
    - Read this to understand Apex Program scenario: How features work and Logic behind them.

02. [Technical Structure](./docs/Structure.md)
    - Read this to understand the code: The Django app structure, directory tree, and technology stack.

03. [Database Schema](https://dbdiagram.io/d/Apex-Program-6946b6944bbde0fd74e30a68)
    - You can visit [dbdiagram](https://dbdiagram.io/) website to see the ERD diagram used for models architecture.

## 🤝 Contributing

Contributions are always welcome!
Checkout [Contributing Guide](./CONTRIBUTING.md) for how to contribute instructions.

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
You are free to use, modify, and distribute this software with proper attribution.
