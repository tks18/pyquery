# 🐍 SDK - The Sorcerer's Grimoire 🔮

Yo, welcome to the deep end. You want to build your own tools on top of our engine? You want to run massive data pipelines from a Jupyter Notebook? You want to interface with the raw metal of PyQuery?

**This is the SDK.** Pure Python. No limits.

## 📦 Installation

```bash
pip install pyquery-polars
```

## 🏎️ The Engine Core

Everything starts with the `PyQueryEngine`. It's the brain that coordinates I/O, memory, and logic.

```python
from pyquery_polars import PyQueryEngine

# Initialize the beast
engine = PyQueryEngine()
```

---

## 💾 I/O Manager (`engine.io`)

The `IOManager` is your gateway to the filesystem. It doesn't just "read files"; it hunts them.

### `load_file(path, **params)`
Load a single file. Supports CSV, Parquet, Excel, JSON, etc.

> **⚠️ NOTE:** This returns a **Tuple** of `(LazyFrame, Metadata)`. You gotta unpack it.

```python
# Simple Load
result = engine.io.load_file("data.csv")
if result:
    df, meta = result
    print(f"Loaded {meta['file_count']} file(s).")
```

### `resolve_files(path, filters=...)`
Find files like a predator.
```python
# Find all CSVs in 'data/' that match regex 'sales_2024_\d+' but NOT 'backup'
files = engine.io.resolve_files(
    path="data/",
    filters=[
        {"type": "glob", "value": "**/*.csv"},
        {"type": "regex", "value": "sales_2024_\d+"},
        {"type": "not_contains", "value": "backup"}
    ]
)
print(f"Found {len(files)} targets.")
```

### `export_sync(lf, format, params)`
Save your work. Supports Parquet, CSV, Excel, JSON, NDJSON, IPC, SQLite.

```python
# Save as Parquet (Compressed)
engine.io.export_sync(
    lf_or_df=df, 
    format="Parquet", 
    params={
        "path": "clean_data.parquet",
        "compression": "zstd"
    }
)
```

---

## 🗄️ Dataset Manager (`engine.datasets`)

Your in-memory registry. Think of it as a dictionary on steroids that syncs with a SQL engine.

### `add(name, lf)`
Register a LazyFrame.
```python
import polars as pl
df = pl.scan_csv("data.csv")

# Add to registry (makes it queryable via SQL too)
engine.datasets.add("sales", df)
```

### `get(name)`
Retrieve a specific dataset as a `LazyFrame`.
```python
df = engine.datasets.get("sales")
# df is now a polars.LazyFrame
```

### `get_all_for_context()`
Get everything. Useful for custom orchestration.
```python
all_data = engine.datasets.get_all_for_context()
for name, lf in all_data.items():
    print(f"Dataset: {name}")
```

---

## 🧠 Processing Manager (`engine.processing`)

Run transformations, SQL, and recipes.

### `execute_sql(query)`
Run SQL against **any** registered dataset. It uses Polars' SQL context under the hood. Returns a `LazyFrame`. ⚡

```python
# Join 'sales' (CSV) and 'targets' (Excel) via SQL
lf_result = engine.processing.execute_sql("""
    SELECT 
        s.region,
        SUM(s.amount) as total_sales,
        AVG(t.target) as avg_target
    FROM sales s
    JOIN targets t ON s.region = t.region
    GROUP BY s.region
""")

# Collect to see results
print(lf_result.collect())
```

### `apply_recipe(lf, recipe)`
Apply a list of transformation steps programmatically.
```python
recipe = [
    {
        "op": "fill_null",
        "params": {"columns": ["amount"], "strategy": "zero"}
    },
    {
        "op": "filter",
        "params": {"column": "amount", "operator": ">", "value": 100}
    }
]

clean_lf = engine.processing.apply_recipe(df, recipe)
```

---

## 📊 Analytics Manager (`engine.analytics`)

Embedded Machine Learning and Statistics. Why leave PyQuery to do ML? We do it faster.

> **⚠️ NOTE:** Most analytics functions rely on **Pandas DataFrames** (materialized data) because they use Scikit-Learn/Scipy internally.

### `get_correlations(df, columns)`
Instant correlation matrix.
```python
# Materialize first
pdf = df.collect().to_pandas()

stats = engine.analytics.get_correlations(
    pdf, 
    num_cols=["amount", "price", "discount"]
)
print(stats) 
# [{'x': 'amount', 'y': 'price', 'r': 0.85}, ...]
```

### `cluster_data(df, features)`
Unsupervised clustering (K-Means) with auto-optimization.
```python
# Find customer segments based on spend and activity
clusters = engine.analytics.cluster_data(
    pdf, 
    features=["total_spend", "visit_count"],
    n_clusters=3
)
print(clusters['labels'])
```

### `detect_anomalies(df, features)`
Find the weirdos using Isolation Forests.
```python
# Find fraudulent transactions
anomalies = engine.analytics.detect_anomalies(
    pdf,
    features=["amount", "transaction_time"],
    contamination=0.01
)
# Returns indices of anomalies
```

---

## 🧪 "God Tier" Workflow Example

Here is a full production script. It finds data, cleans it, registers it, runs SQL to aggregate, applies ML to find anomalies, and exports the suspicious rows.

```python
from pyquery_polars import PyQueryEngine
import polars as pl

def main():
    # 1. Start Engine
    engine = PyQueryEngine()
    
    # 2. Smart Resolve Files
    print("🛰️ Scanning sector...")
    files = engine.io.resolve_files("raw_data/", filters=[{"type": "glob", "value": "**/*.csv"}])
    
    # 3. Load & Union
    print(f"🔫 Target acquired: {len(files)} files.")
    
    loaded_lfs = []
    for f in files:
        res = engine.io.load_file(f)
        if res:
            lf, _ = res
            loaded_lfs.append(lf)
            
    if not loaded_lfs:
        print("❌ No data found.")
        return

    # 4. Register Master Dataset
    master_lf = pl.concat(loaded_lfs)
    engine.datasets.add("transactions", master_lf)
    
    # 5. SQL Aggregation (Lazy)
    print("🧠 Crunching numbers...")
    user_stats_lf = engine.processing.execute_sql("""
        SELECT 
            user_id,
            COUNT(*) as tx_count,
            SUM(amount) as total_spend,
            AVG(amount) as avg_spend
        FROM transactions
        GROUP BY user_id
    """)
    
    # 6. ML Anomaly Detection (Materialize for Scikit-Learn)
    print("🕵️ Hunting anomalies...")
    stats_pd = user_stats_lf.collect().to_pandas()
    
    results = engine.analytics.detect_anomalies(
        stats_pd,
        features=["total_spend", "tx_count"],
        contamination=0.05
    )
    
    # 7. Merge Results & Export
    stats_pd['is_anomaly'] = results['predictions']
    
    # Filter for anomalies
    suspicious_df = pl.from_pandas(stats_pd).filter(pl.col("is_anomaly") == -1)
    
    print(f"🚨 Found {len(suspicious_df)} anomalies.")
    
    # Export to Excel for the Ops team
    engine.io.export_sync(
        suspicious_df,
        format="Excel",
        params={"path": "suspicious_users.xlsx"}
    )
    
    print("✅ Mission Complete.")

if __name__ == "__main__":
    main()
```
