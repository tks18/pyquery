# 💻 CLI - The Command Line Drip 💧

Yo, welcome to the **main event**. If you're reading this, you're probably done with clicking buttons and ready to ascend to **God Mode**. The PyQuery CLI isn't just a tool; it's a weapon. ⚔️

This doc covers **EVERYTHING**. Every command. Every flag. Every edge case. No cap. 🧢🚫

---

## 🧭 The Commands

We got three main modes. Choose your fighter:

| Command | Vibe | Description |
| :--- | :--- | :--- |
| `run` | 🏎️ **Speedrun** | The **Headless Beast**. Runs ETL pipelines in the dark. CI/CD friendly. |
| `ui` | 🎨 **Creative** | Launches the **Streamlit Web App**. Drag-and-drop, charts, vibes. |
| `api` | 📡 **Server** | Starts the **FastAPI Backend**. For when you're building your own app on top of us. |

---

## 🏎️ `pyquery run` (The Headless Speedrun)

This is where the real work happens. Use this to automate your data flows.

### 📚 Syntax
```bash
pyquery run [OPTIONS]
```

### 🎛️ Core Options

#### `--output`, `-o` (Required) 💾
**The Destination.** Where is this data going?
*   **What it does:** Specifies the path for the final processed file.
*   **Example:** `pyquery run -s data.csv -o processed_data.parquet`

#### `--source`, `-s` 📂
**The Origin.** Where is the data coming from?
*   **What it does:** Path to a file, a URL, or a connection string.
*   **Constraint:** You gotta use this if you aren't using `--project`.
*   **Example (File):** `pyquery run -s "C:/Data/sales_2024.csv" -o output.parquet`
*   **Example (URL):** `pyquery run -s "https://example.com/data.json" -o output.parquet`

#### `--type` 🏷️
**The Flavor.** What kind of source is it?
*   **Choices:** `file` (default), `sql`, `api`.
*   **Example (SQL Source):** `pyquery run --type sql --source "postgres://user:pass@localhost/db" --sql-query "SELECT * FROM users" -o users.parquet`

#### `--format`, `-f` 📦
**The Packaging.** How do you want it wrapped?
*   **Choices:** `Parquet` (default/GOAT), `CSV`, `Excel`, `JSON`, `NDJSON`, `IPC`, `SQLite`.
*   **Example:** `pyquery run -s data.parquet -o legacy_data.csv -f CSV`

### 🧠 Advanced Loading (The Big Brain Stuff)

#### `--file-filter` 🔍
**The Bouncer.** Only let specific files in.
*   **Syntax:** `type:value`
*   **Types:** `glob`, `regex`, `contains`, `exact`.
*   **Example:** Only load files starting with "2024":
    ```bash
    pyquery run -s "data_folder/" --file-filter "glob:2024*.csv" -o result.parquet
    ```

#### `--sheet-filter` 📑
**The Excel Whisperer.** Pick specific sheets.
*   **Example:** Only load sheets containing "Finance":
    ```bash
    pyquery run -s annual_report.xlsx --sheet-filter "contains:Finance" -o finance.parquet
    ```

#### `--split-sheets` 🍰
**The Slicer.** Turn one Excel file into many datasets.
*   **What it does:** Instead of smashing everything together, it treats each sheet as a separate table.
*   **Example:** `pyquery run -s report.xlsx --split-sheets -o output_folder/`

#### `--clean-headers` 🧼
**The Sanitizer.** Fix ugly column names.
*   **What it does:** Turns `Customer Name (2024)` into `customer_name_2024`. Snake_case supremacy. 🐍
*   **Example:** `pyquery run -s messy.csv --clean-headers -o clean.parquet`

#### `--auto-infer` 🔮
**The Psychic.** Guess data types so you don't have to.
*   **What it does:** Scans your data and casts strings to ints/dates/floats automatically.
*   **Example:** `pyquery run -s raw_dump.csv --auto-infer -o smart_data.parquet`

### 🧪 Transformations (Cooking)

#### `--sql-query` 🔡
**Source SQL.** The query used to **fetch** data (Source Mode Only).
*   **Example:** `pyquery run --type sql -s "db_url" --sql-query "SELECT * FROM heavy_table LIMIT 1000" -o sample.parquet`

#### `--transform-sql` 🪄
**Post-Load SQL.** Run SQL **on the loaded dataframe** inside PyQuery.
*   **What it does:** Filter/Agg *after* loading but *before* saving.
*   **Example:** `pyquery run -s data.csv --transform-sql "SELECT city, SUM(sales) FROM cli_data GROUP BY city" -o summary.parquet`

#### `--alias` 🏷️
**The Nickname.** Call your dataset something else in SQL.
*   **Default:** `cli_data`
*   **Example:** `pyquery run -s users.csv --alias "users" --transform-sql "SELECT * FROM users WHERE active = true" -o active_users.parquet`

#### `--recipe`, `-r` 🧾
**The Master Plan.** Load a JSON recipe file.
*   **What it does:** Executes a complex list of steps you saved from the UI.
*   **Example:** `pyquery run -s raw.csv -r processing_steps.json -o cooked.parquet`

### 🚀 Project Mode (Enterprise Level)

#### `--project`, `-p` 🏗️
**The Blueprint.** Run a full `.pyquery` project file.
*   **What it does:** Loads multiple datasets, joins, and recipes defined in a YAML/JSON project file.
*   **Example:** `pyquery run --project daily_etl.pyquery -o dist/`

#### `--dataset`, `-d` 🎯
**The Sniper.** Only export specific datasets from a project.
*   **Example:** `pyquery run -p full_project.pyquery -d "Sales_Clean" -d "Marketing_Clean" -o dist/`

#### `--merge`, `-m` 🤝
**The Unifier.** Merge all selected datasets into one output file.
*   **Example:** `pyquery run -p project.pyquery --merge -o combined_report.xlsx`

### 🛠️ Developer / Debug Flags

#### `--dev` 👨‍💻
**God Mode.**
*   **What it does:** Shows verbose logs, stack traces, and skips the intro animation.

#### `--quiet`, `-q` 🤫
**Stealth Mode.**
*   **What it does:** No aesthetic logs. Just errors. Good for cron jobs.

---

## ⚡ God Tier Workflows (Advanced Examples)

You wanted the smoke? Here it is. These commands allow you to do things that would take 300 lines of Pandas code in **one line**.

### 1. The "Recursive Folder Nuke" ☢️
Load ALL CSVs from a nested folder structure that start with `sales_`, clean their headers so they match, auto-infer types, filter for only rows where revenue > 1000, and dump it all into a single compressed Parquet file.

```bash
pyquery run \
  --source "C:/Enterprise/Data/Raw/" \
  --file-filter "glob:**/sales_*.csv" \
  --clean-headers \
  --auto-infer \
  --transform-sql "SELECT * FROM cli_data WHERE revenue > 1000" \
  --output "C:/Enterprise/Data/Clean/master_sales.parquet" \
  --format Parquet \
  --compression zstd
```

### 2. The "Excel Harvester" 🌾
Take a massive multi-sheet Excel file. We only want sheets that contain the word "Region" (e.g., "Region_North", "Region_South"). We want to split them into separate files, but we also want to convert them to JSON for our web frontend. And we want to do it silently because we are running this on a server.

```bash
pyquery run \
  --source "quarterly_dump.xlsx" \
  --sheet-filter "contains:Region" \
  --split-sheets \
  --output "dist/json_api/" \
  --format JSON \
  --quiet
```

### 3. The "SQL Inception" 🤯
Connect to a PostgreSQL database, run a complex join query to get the raw data, THEN (inside PyQuery) calculate a rolling average using Polars logic (via SQL), rename the columns, and save it as an Excel report for management.

```bash
pyquery run \
  --type sql \
  --source "postgresql://admin:hunter2@warehouse.local/prod_db" \
  --sql-query "SELECT date, product_id, sales FROM transactions WHERE date >= '2024-01-01'" \
  --alias "raw_tx" \
  --transform-sql "SELECT date, product_id, sales, AVG(sales) OVER (PARTITION BY product_id ORDER BY date ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) as rolling_7d FROM raw_tx" \
  --output "Weekly_Performance_Report.xlsx" \
  --format Excel
```

### 4. The "Project Sniper" 🔫
You have a massive `.pyquery` project file (`daily_ops.pyquery`) that defines 20 different datasets and transformations. You only need to re-run the `Logistics_Opt` dataset because you tweaked the logic, and you want to output it to CSV for a vendor.

```bash
pyquery run \
  --project "daily_ops.pyquery" \
  --dataset "Logistics_Opt" \
  --output "vendor_drop/" \
  --format CSV
```

---

## 🎨 `pyquery ui` (The Visual Experience)

Launch the web interface.

#### `--port` 🔌
Change the listening port.
*   **Default:** `8501`
*   **Example:** `pyquery ui --port 9090`

#### `--dev` 🛠️
Enable hot-reloading and extra debug info in the browser.
*   **Example:** `pyquery ui --dev`

---

## 📡 `pyquery api` (The Backend Server)

Start the REST API.

#### `--port` 🔌
Change the API port.
*   **Default:** `8000`
*   **Example:** `pyquery api --port 3000`

#### `--reload` 🔄
Auto-restart server when code changes (for devs).
*   **Example:** `pyquery api --reload`

---

## 💡 Pro Tips & Tricks

*   **Combine Flags:** You can stack filters.
    ```bash
    pyquery run -s data/ --file-filter "glob:*.csv" --clean-headers --auto-infer -o clean_data.parquet
    ```
*   **SQL + File:** You can load a CSV and query it immediately.
    ```bash
    pyquery run -s large.csv --transform-sql "SELECT * FROM cli_data WHERE revenue > 1000000" -o high_revenue.csv
    ```

Go forth and automate. 🤖✨
