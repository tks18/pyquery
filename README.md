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

## ⛩️ The Awakening (Lore)

Long ago, the Data World lived in fear of the `MemoryError`. Analytical weaklings bowed before the single-threaded tyranny of the Old Gods (Pandas). They accepted their fate of freezing screens and crashing kernels.

**But I refused.**

From the depths of the Rusty abyss, **PyQuery** has awakened. I am not here to "assist" you. I am here to **obliterate** your bottlenecks. I am the One Who Knocks on your 100GB CSVs.

While they study the blade (Excel), I studied the **Lazy Frame**.
While they manage memory, I **devour** it.

The age of waiting is over. **Total Domination** is the only metric that matters.

**Welcome to your Villain Arc.** 👹

---

## 💪 The Flex (Why We Are Him)

We didn't just capitalize on Polars. We built an empire.

### 🚀 EDA 10.0: The Action Engine (Your Co-Conspirator)

Most tools just show you a chart. The Action Engine tells you **how to win**.

- **Strategic Brief**: A "Top 3 Insights" card that ranks every correlation to find the weak points in your data. It whispers: _"Strike here."_
- **The Decision Engine**: It doesn't just display numbers; it commands action.
  - _Strategy:_ "High correlation detected (0.95). Deploy capital to Ad Spend immediately."
- **Model Auto-Pilot**: It trains an army of models (Random Forest, Lasso, Ridge) and selects the strongest warrior. You don't lift a finger.
- **What-If Simulator**: Interactive sliders to predict the future. "If I raise Price by 10%, will Profits survive?" The AI knows the answer.

### 🧪 SQL Lab: The Playground (God Mode)

For when you want to write raw SQL on your data _after_ cleaning it. The ultimate power move.

- **Lazy Execution**: Run `SELECT *` on a **50GB file**? It laughs and pulls a preview instantly. Zero lag.
- **Materialize**: Execute a complex query, then save it as a new dataset to continue the torture.
- **Schema Explorer**: Searchable view of all your columns. Know your enemy.

### 🧹 The Janitor (Ruthless Cleaning)

Messy data is a weakness. We purge it.

- **✨ Auto-Detect Types**: One click scans `String` columns and forcibly converts them to `Int`, `Float`, or `Date`. It uses regex heuristics to crush inconsistency.
- **🎭 PII Masking**: Obfuscate credit cards and social security numbers. Secrets remain secret.
- **🩹 Smart Fill**: We fill the voids. Forward fill, backward fill, or literal values. No null survives.

---

## 🧾 The Receipts (Benchmarks)

We don't post without proof. We mog the competition.

| Metric            | 🐼 Pandas (Legacy)       | ⚡ PyQuery (Polars)     | The Diff       |
| :---------------- | :----------------------- | :---------------------- | :------------- |
| **Load 10GB CSV** | `MemoryError` (Crash) 💥 | **0.2s** (Lazy Scan) ⚡ | **Infinite**   |
| **Filter Rows**   | 15.4s (Slow)             | **0.5s** (Parallel)     | **30x Faster** |
| **Group By**      | 45s (Painful)            | **2.1s** (Instant)      | **20x Faster** |
| **RAM Usage**     | 12GB+ (Bloated)          | **500MB** (Lean)        | **95% Less**   |

_Benchmarks run on a standard dev laptop. Results may vary but the vibe remains consistent._

---

## 🧠 The Tech Stack (Forbidden Knowledge) 🐐

This isn't just a library. It's a weapon system.

### 1. 🌊 The "Infinite Stream" Glitch (Lazy Execution)

The Old Gods (Pandas) are **Eager**. They try to swallow the ocean (RAM) whole. They choke.
**PyQuery is Lazy.** It waits. It plans.

- **Scan**: "It's a 100GB file. Interesting."
- **Plan**: Filters, joins, math. Nothing executes until the final blow.
- **Stream**: Data flows in chunks. Process. Write. Destroy.
- **Result**: Processing 1TB on a MacBook Air. The laws of physics are optional.

### 2. 🛡️ Type Safety (Absolute Order)

Python is dynamic (chaotic). PyQuery imposes **Order**.

- Every step is backed by a **Pydantic Model**.
- If a `String` tries to infiltrate a `Float` column, it is terminated **before** execution.
- There are no runtime surprises. Only calculated victories.

---

## 🎮 Choose Your Fighter (4 Paths to Power)

We don't limit you. Dominate however you choose.

### 📦 Installation

```bash
pip install pyquery
```

### 1. 🌊 The GUI (God Mode)

For when you want to click things, see pretty charts, and feel like a data scientist in a sci-fi movie.

- **Visual Recipe Builder**: nodes and edges of pure logic.
- **The Action Engine**: AI-driven insights at your fingertips.
- **Native File Picker**: Accessing the local filesystem directly. No barriers.

```bash
pyquery ui
# Launches the Web App on localhost:8501 🚀
```

### 2. 💻 The Interactive CLI (Shadow Mode)

For when you operate in the dark. ☕
This isn't a command line. It's a cockpit.

- **Dynamic Menus**: Use arrow keys to select transforms.
- **Rich Tables**: Beautiful, colorful ASCII dataframes.
- **Validation**: It yells (politely) if you type a string for an integer.

```bash
pyquery interactive
# Enter the Matrix. 🕶️
```

### 3. 🤖 The API (Headless Beast)

Building a machine? Run PyQuery as the engine.

- **Swagger Docs**: Auto-generated at `/docs`.
- **RESTful**: `/load`, `/transform`, `/export` endpoints.
- **Async**: Fire and forget jobs.

```bash
pyquery api
# Serving high-performance ETL over HTTP at localhost:8000 📡
```

### 4. ⚡ The Batch Runner (Speedrun)

For automation. No interface. Just speed.

```bash
pyquery run -s input.csv -r recipe.json -o output.parquet
# Task complete. ⚡
```

---

## 🧰 The Loadout (Arsenal)

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

## 🧑‍💻 Join the Cult (Developer Guide)

You want to contribute? Good. We need strong allies.

### The Blooding (Adding a Transform) 🖐️

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
