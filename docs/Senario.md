# 📜 Scenario & Game Mechanics

---

## 1. The Player (User)

The user is the sole `Player` of the system. The goal is to maximize the player's `Level` and `Stats` through real-world actions.

Every human has long-term, mid-term and short-term plans, wishes to improve each dimension of life, and develop good habits and routines. The System, named the **Apex Program** will help you do that.

### Leveling Logic

As a player you will start the Apex program at **Level 1**. Each task you complete, habit or routine you do each day, or a dungeon you clear will grant you **XP (experience)**. Your level requires a certain amount of these XPs in order to level up.

The amount of XP you will need to level up to the next level is calculated through the `XP curve Formula`.

#### XP Curve Formula

$$
XP_{Raw} = 100 \times (1.06)^{\text{Current Level}}
$$

$$
XP_{Required} = \lceil \frac{XP_{Raw}}{100} \rceil \times 100
$$

*The system calculates the raw XP, then rounds it **up** to the nearest 100 (e.g., 12,345 becomes 12,400) for a cleaner progression.*

- **Novice Protection:** The minimum XP required is naturally clamped to **100** by the rounding formula.
- **End-Game Cap:** The maximum XP per level is capped at **30,000** to ensure even high levels are achievable within a human lifetime.
- **Leveling Up:** When you reach the required XP, a popup window appears with your rewards. **You cannot continue using the System until you collect your rewards.**
- **Reward:** Gaining a level grants **+3 Ability Points (AP)** . These APs will be used to upgrade your stats (read [Attributes (Stats)](#2-attributes-stats) section).

### Ranks

Just like the Solo Leveling anime, everything has a rank. Your personal rank is determined by your Level.

| Levels   | Rank      | Title          |
| -------- | --------- | -------------- |
| 1 - 10   | E-Rank    | Novice         |
| 11 - 25  | D-Rank    | Rookie         |
| 26 - 45  | C-Rank    | Elite          |
| 46 - 70  | B-Rank    | Commander      |
| 71 - 80  | A-Rank    | Master         |
| 81 - 90  | S-Rank    | Sovereign      |
| 91 - 99  | SS-Rank   | National Level |
| 100+     | Monarch   | Shadow Monarch |

---

## 2. Attributes (Stats)

Each aspect of life will be tracked by the system under 5 main stats:

- **`STR` (Physique):** Gym, Posture, Sleep, Nutrition, Health, and everything related to your body and physique.

- **`INT` (Intellect):** University, Coding, Math, Reading, Study, and everything related to your brain and intelligence.

- **`CHA` (Charisma):** Social Skills, Networking, Grooming, Negotiation, and everything which gives you more power in social dynamics.

- **`WIL` (Discipline):** Habit streaks, Routine adherence, and everything which requires commitment.

- **`WIS` (Psyche):** Meditation, Journaling, Emotional control, and everything related to your mental health.

**XP Source Tracking:** While XP is generic, the system tracks the source of that XP. To ensure your character build reflects your actual life:

1. **Mandatory Stat Tagging:** Every Task, Habit, or Dungeon **must** be assigned a primary Related Stat.

2. **Affinity Lock:** You are **forbidden** from leveling up a stat that has very low affinity percentage for the current level.
    - **Threshold Rule:** You can spend 1 AP on any stat that contributed **at least 15%** to this level's XP.
    - *Example:* If you spent the entire level coding and one pushup (99% `INT` vs 1% `STR` affinity), you cannot spend your AP on `STR`. You must spend it on INT.

**The Affinity Chart:** When leveling up, the system displays a chart showing:

1. **Current Level Affinity:** What % of XP for this specific level came from which stat?

2. **Lifetime Affinity:** What is your overall character build percentage?

**Reasoning:** You are required to write a short reason why the chosen stat is worthy of an upgrade.

---

## 3. Time Horizons (Life Planning)

The system structures life plans into four layers to manage goals from **"Lifetime"** down to **"Today"**.

### The Vision

- **Scope:** 15 - 25 Years.
- **Concept:** Massive, life-defining trajectories (e.g., "Become an AI Company CEO", "Get Married").
- **Structure:** Vision contains multiple **`Questlines`**.
- **Mechanic:** Visions are managed under the `Conquest` tab. The description is your personal manifesto for that future.

### Questlines

- **Scope:** 5 - 15 Years.
- **Concept:** Breakdown of visions (e.g., "Graduate from Management University", "Immigration").
- **Structure:** Each Questline contains multiple `Dungeons`.

### Dungeons

See the **[Conquest](#4-conquests-dungeons)** section.

### The Arcs (Themes)

- **Scope:** 1 Month - 1 Season.
- **Concept:** A specific period of focus (e.g., "The Awakening Arc", "Comeback Arc").
- **Mechanic:** Arcs act as a Filter. They name your current life chapter.
- **Focus Mode:** You can highlight specific active Dungeons relevant to the current Arc to prioritize them on your dashboard.

### Red Gates (Objectives)

**Scope:** Within an Arc.
**Concept:** High-priority, inescapable checkpoints.
**Mechanic:** Pinned to the Dashboard. These represent the "Boss" of the current month.

---

## 4. Conquests (Dungeons)

Projects (e.g., "Launch App", "Get Degree") are treated as Dungeons.

### Mechanics

The Dungeons mechanics are so similar to the Trello app.

### Views

- **Mobile:** Accordion List
- **Desktop:** Kanban Board

### Stages

- **Scout:** Goal setting. You are examining the dungeon and defining the target tasks.
- **Entry (First Floor):** Commitment. You have formally started working on this dungeon.
- **Mid-Boss:** Though times. Triggered automatically as soon as the first C or higher rank task is completed.
  - Mid-Bosses are strictly for C-Rank Dungeons and above, or if the Task Rank overrides the Dungeon Rank.
- **Boss (Boss Floor):** Climax. You are putting all effort into finalizing the project.
- **Clear:** Victory! The project is 100% complete. Rewards are distributed.
- **Failed:** Defeat... The deadline and emergency timer was missed and the break penalty was fully realized.
- **Abandoned:** Cancelled by choice. The dungeon was deliberately set aside.

### Dungeon Ranks and XP

| Rank      | Finishing Reward | Description                                                                                                                          |
| --------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| E-Rank    | 1,500 XP         | **Short-term Sprints:** Simple, low-risk projects completed in 1-2 weeks (e.g., "Clean Garage", "Setup Coding Environment").         |
| D-Rank    | 4,000 XP         | **Monthly Goals:** Routine milestones or establishing a new habit loop (e.g., "Finish 1 Online Course", "Lose 2kg").                 |
| C-Rank    | 7,500 XP         | **Quarterly Projects:** Standard conquests requiring planning and sustained effort (e.g., "Build Portfolio Website", "Run 10km").    |
| B-Rank    | 10,000 XP        | **Major Challenges:** High-pressure or critical path milestones (e.g., "Land an Internship", "Release App MVP").                     |
| A-Rank    | 15,000 XP        | **Life Milestones:** Significant breakthroughs that take 6+ months (e.g., "Get University Degree", "Get Married").                   |
| S-Rank    | 20,000 XP        | **Grand Ambitions:** Massive, multi-year undertakings with high risk (e.g., "Reach $100k Net Worth", "Obtain Senior Role").          |
| SS-Rank   | 30,000 XP        | **Legacy Achievements:** "National Level" feats that define a decade (e.g., "Buy a House", "Start a Successful Company").            |
| Monarch   | 60,000 XP        | **The Final Vision:** The ultimate culmination of your life's work or "Life Purpose" (e.g., "Financial Freedom", "Industry Leader"). |

### ☠️ The Dungeon Break (Time Limit Failure)

A specific penalty triggers **only if you set a Deadline and let the timer run out!**

1. **Deadline Missed:** Dungeon enters **BOSS RAID** mode (Red Alert).
2. **Emergency Timer:**  A second, final countdown begins. You must clear the dungeon within this time.

    | Dungeon Rank | Emergency Timer |
    | ------------ | --------------- |
    | E-Rank       | 1 Day           |
    | D-Rank       | 2 Days          |
    | C-Rank       | 3 Days          |
    | B-Rank       | 5 Days          |
    | A-Rank       | 1 Week          |
    | S-Rank       | 2 Weeks         |
    | SS-Rank      | 3 Weeks         |
    | Monarch      | 1 Month         |

3. **XP Decay:** The reward drops linearly as the emergency timer ticks down.
4. **BREAK (True Failure):** Both **deadline and emergency** timer hits 0.
    - **The Consequence:** The dungeon has broken and you failed to beat the released monsters!
    - **Penalty:** When setting a deadline, you **must** link specific Stats to the Dungeon. These stats will be **De-leveled** upon failure.
    - **Penalty Severity (Per linked Stat)**
        - **Monarch/SS:** -5 Levels
        - **S-Rank:** -3 Levels
        - **A-Rank:** -2 Levels
        - **E/D/C-Rank:** -1 Levels

    - **Logic:** "Use it or lose it."

### 🏳️ Strategic Withdrawal (Manual Failure)

In life, priorities change. A goal may no longer be relevant, or the cost of pursuing it may outweigh the benefits. You have the option to manually mark a Dungeon as `Failed` (Abandoned).

- **The Reflection Protocol:** Upon abandoning a dungeon, the System will prompt you to input a **Reason for Failure**.

- **The Wisdom Bonus:** If you provide a thoughtful reason (post-mortem analysis), the System treats this as a learning experience.

  - **No Penalty:** You will suffer **zero** stat penalties.

  - **Consolation Rewards:** You will earn a small amount of `WIS` (Psyche) and `INT` (Intellect) XP, symbolizing the wisdom gained from knowing when to quit.

***!!! System Warning:*** You must manually Withdraw from a dungeon **before the Emergency Timer starts** to avoid the penalty. Once the Break occurs, the damage is done.

---

## 5. Tasks, Habits, and Routines

### Tasks

Single, one-time actions that require effort and time (e.g., "Write Chapter 1", "Fix Bug #404"). Tasks can be linked to Dungeons or stand alone.

### Habits

Recurring actions performed on a specific schedule (e.g., "Gym: Mon/Wed/Fri", "Read: Daily"). Streaks are tracked to boost `WIL` and `consistency`.

### Routines

A set of Habits or simple actions grouped together to be performed in sequence (e.g., "Morning Routine": Make Bed -> Drink Water -> Meditate).

### Task Ranking Algorithm

Every task, habit, or routine is assigned a **Complexity Score** to determine its Rank (E to Monarch Level) and XP Reward.

**Options:**

1. **Manual:** You will choose the task's rank manually.
2. **System Estimation:** The system will predict the tasks rank for you based on the logic explained below.

#### System Rank Estimation Logic

The system will calculate a score for the task using this formula:

$$
Score = [(Duration \times 0.25) + (Effort \times 1.5) + (Impact^{3})] \times FearFactor
$$

- **Duration:** Scale of **2 to 40**.
  - < 15 mins = 2 pts
  - 30 mins = 5 pts
  - every 1 hour = 10 pts
  - 4 hours and above = 40 pts (Max)
- **Effort:** Intensity scale of **1 to 10**.
- **Impact:** Exponential weight. **Life-changing** tasks are worth significantly more. **(1 to 5)**
- **Fear Factor:** Multiplier **(1.0 - 2.0)** for tasks that induce psychological resistance (e.g., Cold Calling).
  - **1.0:** Routine.
  - **1.5:** Anxiety-inducing.
  - **2.0:** Terrifying.

| Score Range  | Rank    | Base XP | Description                                    |
| ------------ | ------- | ------- |--------------                                  |
| 3 - 20       | E-Rank  | 15 XP   | Simple Maintenance (Brush Teeth, Make Bed)     |
| 21 - 45      | D-Rank  | 35 XP   | Routine Work (30m Study, Gym)                  |
| 46 - 75      | C-Rank  | 75 XP   | Standard Quest (Deep Work, Long Study)         |
| 76 - 120     | B-Rank  | 150 XP  | Challenge (Project Milestone, Complex Bug Fix) |
| 121 - 180    | A-Rank  | 350 XP  | Major Feat (Launch MVP, Ace Final Exam)        |
| 181 - 250    | S-Rank  | 700 XP  | Nightmare Quest (High Fear **or** High Impact) |
| 251 - 280    | SS-Rank | 1200 XP | National Level (High Fear **and** High Impact) |
| 281+         | Monarch | 1500 XP | Shadow Monarch (Buy House, Exit Startup)       |

---

## 6. The Library

The Library is your personal repository of knowledge, designed to track reading, courses, and research. It is the primary engine for accumulating `INT` (Intellect) XP.

### Books & Resources

Everything you read or study is treated as a "Book" in the system, even if it is an online course or a technical documentation.

- Track **Duration** (minutes).
- Track **Pages/Progress** covered.

#### Book Stages

- **Wishlist:** Books you intend to acquire.
- **Acquired (On Shelf):** Books you own but haven't started.
- **Reading:** Currently active resources.
- **Completed:** Finished books.
- **Dropped:** Abandoned books (no XP reward).

### Knowledge Rank

Books are ranked by their complexity and density. Finishing a book grants a "Completion Bonus" based on its rank.

| Book Rank | Completion Bonus  | Type of Content                          |
| --------- | ----------------  |------------------------------------------|
| E-Rank    | 50 XP             | Light Novel, Manga, Casual Articles      |
| D-Rank    | 150 XP            | Self-Help, Biographies, Simple Fiction   |
| C-Rank    | 400 XP            | Technical Manuals, Textbooks (Undergrad) |
| B-Rank    | 1000 XP           | Advanced Technical, Scientific Papers    |
| A-Rank    | 2500 XP           | PhD Thesis, Complex Philosophy           |
| S+ Rank   | 6000+ XP          | "Forbidden Knowledge" (Life's Work)      |

---

## 7. Hall of Glory

A dedicated archive to immortalize your victories, titles, and major milestones. This section is purely for morale and legacy tracking.

### Titles

Special designations you earn by completing specific Questlines or achieving stats milestones. You can choose one "Equipped Title" to display on your dashboard profile.

- **Logic:** Earning a title does not grant stats, but it validates your identity change.
- **Examples:**

  - AI Product Manager (Earned by completing the "Get Hired" Questline).
  - Marathon Runner (Earned by running 42km in the Fitness Dungeon).
  - Polymath (Earned by reaching Level 50 in `INT`).

### The Trophy Room (Cleared Dungeons)

A visual gallery of every **S-Rank** and **SS-Rank** Dungeon you have successfully cleared.

- Displays the Dungeon Name, Clear Date, and Final Reward.
- Serves as a reminder of the "Monsters" you have defeated in real life.

### Feats of Strength

Automated badges awarded by the system for consistency and grinding.

- **Iron Will:** Maintain a habit streak for 100 days.
- **Awakened:** Reach Level 10.
- **Scholar:** Read 10,000 pages total.
- **Wealthy:** Accumulate a specific net worth in the Inventory module.

---

## 8. Inventory (Wealth & Assets)

This section is for tracking "What I Have." It manages your financial stats and physical possessions.

### Gold (Liquid Wealth)

- **Income:** Monthly salary, freelance earnings, and side hustles.
- **Savings:** Tracking specific saving goals/accounts.
- **Financial Activities:** A ledger for investments and major expenditures.

### Equipment (Assets)

Significant physical items that empower you.

- **Home:** Apartment/House.
- **Mounts:** Car, Motorcycle, Bicycle.
- **Gear:** Laptop (e.g., RTX 3060ti), Phone, Musical Instruments.

### Consumables

Items purchased to boost stats or improve well-being.

- **Types:** Supplements, Nootropics, Vitamins.
- **Status Tracking:** `New` -> `Used` -> `Low` -> `Empty`.
- **Clothing & Perfumes:** Tracked here as well (Perfumes are consumable, Clothes are permanent assets).

### Shopping List

A wishlist of future items you intend to buy to upgrade your lifestyle or stats.
