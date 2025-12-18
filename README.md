# ⚡ PyQuery: The ETL GOAT 🐐

> **Author**: [Sudharshan TK](https://github.com/tks18)  
> **Vibe Check**: Passed ✅  
> **Status**: Main Character Energy ✨

Yo, welcome to **PyQuery**. If you're still doing ETL in Excel or struggling with slow python scripts, **it's giving struggle bus**. 🛑 I built this to make data engineering feel less like a chore and more like a vibe.

Powered by **Polars** 🐻‍❄️, so it handles big data faster than you can say "Runtime Error".

---

## 🧐 What's the Tea? 🍵

PyQuery is a low-code ETL app that actually **slaps**. We ditched the legacy sluggishness for pure speed and aesthetics.

- **Import Anything**: CSV, Excel, Parquet, SQL, API... if it exists, we claim it.
- **Transformation Rizz**: Filter, Join, Pivot, Window Functions, Dedupe. We got the whole toolkit.
- **Visual Recipe**: Build your pipeline steps like a Spotify playlist. 🎶
- **Export Everywhere**: Send your clean data back to SQL, or dump it as Parquet/Excel/CSV.

---

## ✨ Features (The Flex) 💪

Why use PyQuery? because doing it manually is **cringe**.

| Feature | Lowkey Amazing Because... |
| :--- | :--- |
| **Polars Engine** ⚡ | It's faster than your ex replying. 100x speedup over pandas. |
| **Toxic Data Cleanup** 🧹 | Our "Robust Cast" features fix broken dates/numbers automatically. No more `ValueError`. |
| **SQL & API Input** 🔗 | We connected. Postgres, MySQL, APIs... we tap into everything. |
| **Dedupe & Sample** 🧪 | Yeet the duplicates and test with samples. Quality > Quantity. |
| **Window Functions** 🪟 | Rolling averages & ranks made easy. Big brain analytics. 🧠 |
| **Threaded Export** 🧵 | Exports run in the background so the UI doesn't freeze. Multitasking king/queen. |
| **Auto-Profiling** 📊 | We stalk your data (metadata only) and give you the tea on nulls & distributions. |

---

## 🛠️ Stack Check (The Drip) 💧

Built with the absolute units of the python ecosystem:
- **Streamlit**: The UI King.
- **Polars**: Speed Demon (Rust power 🦀).
- **ConnectorX**: Reading SQL at the speed of light.
- **Request**: For fetching that API goodness.

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
   - Click **➕ Join** to link up with other datasets (Left, Inner, Cross... take your pick).
   - Click **➕ Dedupe** to clean up the mess.
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

GPL-V3. We don't gatekeep.

---
*Made with ☕ and 💖 by Sudharshan TK*
