<div align="center">

# ⚡ PyQuery: The ETL Beast 🐐

[![Status](https://img.shields.io/badge/Status-Main_Character_Energy-%23FF0055?style=for-the-badge&logo=appveyor)](https://github.com/tks18/pyquery)
[![RAM Usage](https://img.shields.io/badge/RAM_Usage-Low_Key_Zero-%2300ffa3?style=for-the-badge&logo=nvidia)](https://pola.rs)
[![Engine](https://img.shields.io/badge/Engine-Polars_Supremacy_🐻‍❄️-%23ffcc00?style=for-the-badge&logo=polars)](https://pola.rs)
[![Vibe](https://img.shields.io/badge/Vibe-Immaculate_✨-%238A2BE2?style=for-the-badge)](https://github.com/tks18/pyquery)
[![Backend](https://img.shields.io/badge/Backend-FastAPI_🚀-%23009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![PyPI Version](https://img.shields.io/pypi/v/pyquery-polars.svg?color=4CAF50&logo=python&logoColor=white)](https://pypi.org/project/pyquery-polars/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyquery-polars.svg?color=blue)](https://pypi.org/project/pyquery-polars/)
[![License](https://img.shields.io/github/license/tks18/pyquery.svg?color=orange)](LICENSE)

**Your laptop fan shouldn't sound like a Boeing 747. ✈️**<br>
**PyQuery** processes **100GB files** while you watch Netflix. No cap. 🧢

[Feature Request](https://github.com/tks18/pyquery/issues) · [Report Bug](https://github.com/tks18/pyquery/issues)

</div>

---

## 📖 The Lore (Why this exists)

Let's keep it 100. **Pandas is cooked.** 💀

`MemoryError` is tired. Laptops freezing on 2GB CSVs is tired. Writing 50 lines of boilerplate to rename a column gives **NPC energy**.

The goal was a tool that:

1.  **Mogs Big Data**: Handles 100GB+ files without sweating.
2.  **Looks Good**: Because staring at a terminal from 1995 is **cheugy**.
3.  **Just Works**: No "dependency hell". No "setup rituals". Instant gratification via `pip install`.

Enter **PyQuery**. The **Gigachad Data Engine** vs the **Virgin Excel Sheet**.

---

## 🧠 The Tech Stack (Goated Status) 🐐

This isn't just a library wrapper. It's an architected system that **hits different**.

### 1. 🌊 The "Infinite Stream" Glitch (Lazy Execution)

Most tools (Pandas, Excel) are **Eager**. They try to load the entire file into RAM.
_Result_: RAM fills up, swap file explodes, and PC takes a screenshot. 📸

**PyQuery is Lazy.**

- **Step 1 (Scan)**: Reads the file header. "Okay, it's a 50GB file. Bet."
- **Step 2 (Plan)**: You add filters, joins, math. Nothing runs yet. A logical plan is built.
- **Step 3 (Stream)**: When "Export" is hit, data flows in **Chunks** (e.g., 50MB at a time).
  - Chunk comes in ➡️ Process ➡️ Write to Output ➡️ Delete from RAM.
  - Repeat.

**The Flex**: Process a **100GB dataset** on an **8GB MacBook Air**. The RAM usage stays flat line. 📉

### 2. 🛡️ Type Safety (No 'NoneType' errors)

Python is dynamic (unsafe). PyQuery makes it strict.

- Every single step is backed by a **Pydantic Model**.
- If a `String` is put into a `Float` column, the app stops it **before** execution.
- No more waking up to a failed job at 3 AM. L's are caught early.

### 3. 🧩 The Decoupled Core

The brain (Engine) is split from the face (UI).

- **Engine**: Pure Python/Rust (Polars). Fast AF.
- **API**: FastAPI wrapper for headless access.
- **UI**: Streamlit for the visual learners.
- **CLI**: Rich/Questionary for the terminal hackers.

---

## 🎮 Choose Your Fighter (4 Modes)

**v1.3.0** includes **EVERYTHING**. One command to rule them all.

### 📦 Installation

```bash
pip install pyquery
```

### 1. 🌊 The GUI (God Mode)

For when you want to click things, see pretty charts, and feel like a data scientist in a sci-fi movie.

- **Visual Recipe Builder**: Drag & drop transforms.
- **Instant Profiling**: histograms, null counts, distinct values.
- **Export Manager**: Download clean data instantly.

```bash
pyquery ui
# Launches the Web App on localhost:8501 🚀
```

### 2. 💻 The Interactive CLI (Hacker Mode)

For when you're in a coffee shop and want to look busy. ☕
This isn't your dad's command line. This is a **Text User Interface (TUI)**.

- **Dynamic Menus**: Use arrow keys to select transforms.
- **Rich Tables**: Beautiful, colorful ASCII dataframes.
- **Validation**: It yells (politely) if you type a string for an integer.

```bash
pyquery interactive
# Enter the Matrix. 🕶️
```

### 3. 🤖 The API (Headless Beast)

Building a SaaS? Integrating with Airflow?
Run PyQuery as a **Microservice**.

- **Swagger Docs**: Auto-generated at `/docs`.
- **RESTful**: `/load`, `/transform`, `/export` endpoints.
- **Async**: Fire and forget jobs.

```bash
pyquery api
# Serving high-performance ETL over HTTP at localhost:8000 📡
```

### 4. ⚡ The Batch Runner (Speedrun)

CI/CD integration? Cron jobs?
Run a saved JSON recipe on a file and exit. No UI overhead. Pure speed.

```bash
pyquery run -s input.csv -r recipe.json -o output.parquet
# Done before you can blink. ⚡
```

---

## 💧 Fresh Drops (New in v1.3.0)

**SQL Lab** is now live and absolutely cracked. 🔨

- **SQLContext Integration**: All loaded datasets effectively become SQL tables. No boilerplate.
- **Lazy Execution**: Write `SELECT *` on a 50GB file? It only pulls the preview. Zero lag.
- **Hybrid Export**: Run a massive JOIN in SQL and export straight to Parquet/Excel.
- **Full Toolkit**: The vault is unlocked. PII Masking, Smart Extract (Emails/URLs), One-Hot Encoding — it’s all here.

---

## 🔮 The Manifest (Roadmap)

The evolution continues into a **Deterministic, Lazy-First Execution Engine**. The UI is just the side character; the Backend is the Main Character. 🌟

### 🔹 Milestone 1: The Trust Arc (Core Foundation)

**Goal**: No flakes. Trust the process.

- **DAG Execution**: Turning recipes into immutable execution graphs. Structure is key.
- **Fingerprinting**: Receipts are kept. Inputs, schema, version—everything is tracked. If the inputs match, the output matches.
- **Logs that don’t gaslight**: Row counts, timings, warnings. Full transparency on every step.

### 🔹 Milestone 2: Fit Check (Schema & Types)

**Goal**: Strict vibes only. No sloppy types.

- **Explicit Contracts**: Define the schema upfront. No situational situationships with data.
- **Drift Detection**: Know when data changes (new columns, mixed types). 🚩
- **Validation**: Checks the vibe before executing a single row.

### 🔹 Milestone 3: Galaxy Brain (Intelligence)

**Goal**: Work smarter, not harder.

- **Smart Resource Management**: Ball on a compute budget. Predicate pushdowns are pushed to the absolute limit.
- **Smart Caching**: Intermediate steps live rent-free in RAM to avoid re-computing.
- **Data Diffs**: The "Before & After" pics for data changes.

### 🔹 Milestone 4: Polyglot Rizz (SQL & Hybrid)

**Goal**: Speaking everyone's language.

- **SQL to IR**: Converting SQL queries into Polars Internal Representation.
- **Hybrid Pipelines**: Pipe SQL results into a GUI recipe, then back to SQL. Best of both worlds.

### 🔹 Milestone 5: The Grind (Incremental Props)

**Goal**: Production scale or nothing.

- **Incremental Processing**: Upserts, appends, SCDs. Only process what's new.
- **Resume Capability**: Failed job at 99%? Pick up exactly where you left off. Second chances are real.

### 🔹 Milestone 6: Squad Goals (Extensibility)

**Goal**: Bringing the whole ecosystem.

- **Plugin System**: Bring custom steps. Gatekeep nothing.
- **Connector Abstractions**: Read from S3, Postgres, Snowflake — expanding the circle.

---

## 💹 Benchmarks (Receipts) 🧾

| Metric            | 🐼 Pandas (Legacy)       | ⚡ PyQuery (Polars)     | The Diff       |
| :---------------- | :----------------------- | :---------------------- | :------------- |
| **Load 10GB CSV** | `MemoryError` (Crash) 💥 | **0.2s** (Lazy Scan) ⚡ | **Infinite**   |
| **Filter Rows**   | 15.4s (Slow)             | **0.5s** (Parallel)     | **30x Faster** |
| **Group By**      | 45s (Painful)            | **2.1s** (Instant)      | **20x Faster** |
| **RAM Usage**     | 12GB+ (Bloated)          | **500MB** (Lean)        | **95% Less**   |

_Benchmarks run on a standard dev laptop. Results may vary but the vibe remains consistent._

---

## 🧰 The Toolkit (Loadout)

Packed with every tool needed to clear the map.

| Category      | The Tools                                 | Why it slaps                            |
| :------------ | :---------------------------------------- | :-------------------------------------- |
| **Cleaning**  | `Fill Nulls`, `Mask PII`, `Smart Extract` | Turns garbage data into gold. ✨        |
| **Analytics** | `Rolling Agg`, `Time Bin`, `Rank`, `Diff` | High-frequency trading vibes. 📈        |
| **Combining** | `Smart Join`, `Concat`, `Pivot`           | Merge datasets without the headache. 🤝 |
| **Math**      | `Log`, `Exp`, `Clip`, `Date Offset`       | For the scientific girlies. 👩‍🔬          |
| **Text**      | `Slice`, `Case`, `Replace`                | String manipulation on steroids. 💪     |
| **I/O**       | `CSV`, `Parquet`, `Excel`, `JSON`, `IPC`  | Speaks every language. 🗣️               |

---

## 🧑‍💻 Developer Guide (Join the Cult)

Want to add a feature? It's open source. **Fork it.**

### Adding a new Transform (The 5-Step Method) 🖐️

#### Backend Implementation

1.  **Define Params**: Create a Pydantic model (`src/pyquery_polars/core/params.py`).
2.  **Backend Logic**: Write a pure polars function (`src/pyquery_polars/backend/transforms/`).
3.  **Register**: Add your step to `register_all_steps()` in `src/pyquery_polars/backend/engine/registry.py`.

#### Frontend Implementation

1. **Frontend Renderer**: Create a Renderer Function (`src/pyquery_polars/frontend/steps/`).
2. **Register**: Add your step to `register_frontend()` in `src/pyquery_polars/frontend/registry_init.py`.

It appears in the CLI, API, and UI **automatically**. 🤯

```python
# Only certified ballers contribute code.
# Are you up for it?
```

---

## 📜 License

**GPL-3.0**. Open source forever. 💖

---

<div align="center">

_Made with ☕, 🦀 (Rust), and 💖 by [Sudharshan TK](https://github.com/tks18)_

</div>
