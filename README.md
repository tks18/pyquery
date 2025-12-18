<div align="center">

# ⚡ PyQuery: The ETL GOAT 🐐

[![Status](https://img.shields.io/badge/Status-Main_Character_Energy-%23FF0055?style=for-the-badge)](https://github.com/tks18/pyquery)
[![Vibe Check](https://img.shields.io/badge/Vibe_Check-Passed_✅-%2300ffa3?style=for-the-badge)](https://github.com/tks18/pyquery)
[![Engine](https://img.shields.io/badge/Powered_By-Polars_🐻‍❄️-%23ffcc00?style=for-the-badge)](https://pola.rs)

**Stop writing spaghetti code. Start building pipelines that slap.** 🍝➡️🔥

[Feature Request](https://github.com/tks18/pyquery/issues) · [Report Bug](https://github.com/tks18/pyquery/issues)

</div>

---

## 🧐 What's the Tea? 🍵

Yo, welcome to **PyQuery**. If you're still manually cleaning CSVs in Excel or waiting 10 minutes for a Pandas script to run, **it's giving struggle bus**. 🛑

I built this because data engineering shouldn't feel like a 9-5 chore. It should feel like a vibe. PyQuery is a **Low-Code ETL** app that lets you clean, transform, and ship data efficiently. It's built on **Polars**, so it's blazingly fast (Rust power, Iykyk 🦀).

---

## 🆚 The Vibe Check (Comparison)

Why switch? Because we simply built different.

| Feature | 👴 Boomer Tools (Excel/Pandas) | ⚡ PyQuery (The New Wave) |
| :--- | :--- | :--- |
| **Speed** | Slow af. CPU fan goes brrr. 🐢 | **Fast af.** Multithreaded & Lazy. 🐆 |
| **UI** | 1998 called, they want their UI back. | **Clean & Minimal.** Dark mode ready. 🌑 |
| **Usage** | Requires a PhD in formulas. | **Click buttons.** Like a game. � |
| **Crash Rate** | High. "Not responding..." 💀 | **Low.** Streaming engine handles GBs. 💪 |

---

## ✨ Features (The Flex) 💪

We got the toolkit to handle your toxic data.

### 🔌 **Connect Anything**
- **Files**: CSV, Excel, Parquet, JSON. Drag & drop.
- **SQL**: Directly tap into Postgres/MySQL. We speak database.
- **API**: Fetch JSONs from the web. We global. 🌐

### 🧪 **Transformation Rizz**
- **Dedupe**: Yeet the duplicates instantly.
- **Filter**: Banish the bad rows. Ghost them. 👻
- **Joins**: Merge datasets like it's a collab. (Left, Inner, Cross, Anti).
- **Window Funcs**: Rolling averages, ranks, lag/lead. Big brain analytics. 🧠

### 🧹 **Toxic Data Cleanup**
- **Robust Cast**: Fix broken dates, mixed numbers, and messy strings automatically.
- **Standardize NULLs**: Turn those weird "NA", "null", "-" into actual NULLs.

### 🏭 **Production Ready**
- **Recipe Mode**: Build a pipeline of steps. Replay it anytime.
- **Threaded Export**: Exports happen in the background. Keep working while it saves.
- **SQL Export**: Push clean data straight to your Data Warehouse. Current mood: ELT.

---

## 🛠️ The Tech Stack (The Drip) 💧

Built with the absolute units of the python ecosystem.

- **[Streamlit](https://streamlit.io)**: The UI King. 👑
- **[Polars](https://pola.rs)**: The engine. Speed demon. 🏎️
- **[ConnectorX](https://github.com/sfu-db/connectorx)**: Reading SQL at the speed of light.
- **[Requests](https://pypi.org/project/requests/)**: For that API connection.

---

## 🚀 How to Run

Don't be basic. Get this running in seconds.

### 1. Clone the repo
You know the drill.
```bash
git clone https://github.com/tks18/pyquery.git
cd pyquery
```

### 2. Install deps
We use `uv` because life is too short for slow installs.
```bash
uv sync
# OR be retro with pip
pip install -r requirements.txt
```

### 3. Launch it
Let's gooo! 🏎️
```bash
streamlit run app.py
```

---

## 👨‍🍳 Let Him Cook (Usage Guide)

1. **Load Data**:
   - Drag & drop a CSV.
   - Or paste a SQL URI like a hacker. `postgresql://user:pass@localhost:5432/db`
2. **Build the Recipe**:
   - Click **➕ Filter** to banish bad rows.
   - Click **➕ Join** to link up with other datasets.
   - Click **➕ Clean/Cast** to fix types.
3. **Check the Vibes**:
   - Look at the "Live Preview". Changes happen instantly (Lazy execution ftw).
4. **Secure the Bag (Export)**:
   - Export to SQL to save it for production.
   - Or dump to Parquet for that sweet compression.

---

## 🤝 Contributing

**PRs are welcome.**
- Found a bug? **L.** Open an issue.
- Fixed it? **W.** Submit a PR.
- Added a feature? **Goated.**

## 📜 License

**GPL-3.0**. We don't gatekeep. Open source forever. 💖

---
<div align="center">

*Made with ☕ and 💖 by [Sudharshan TK](https://github.com/tks18)*

</div>
