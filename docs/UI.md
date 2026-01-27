# 🎨 User Interface - The Easy Mode

Yo, welcome to the PyQuery UI. This is where you can click buttons and make things happen. It's built on Streamlit, so it's snappy and looks fire.

## 🏠 The Layout

When you launch the app (`pyquery ui`), you'll see a clean interface.

### ⬅️ The Sidebar (Control Center)
This is where you load your data.
*   **File Loader**: Drag and drop your CSVs, Excels, or Parquets here. We support multi-file uploads, so don't be shy.
*   **Dataset List**: See what's currently loaded in memory. Click to switch context.

### 🍴 Recipe & Preview (The Kitchen)
This is the default tab.
*   **Data Preview**: See the first 1000 rows of your data.
*   **Transforms via Column Headers**: Click a column header to filter, sort, or rename.
*   **Recipe Editor**: Add steps manually if you're feeling spicy.
*   **Export**: When you're done cooking, download your data as Parquet, CSV, or Excel.

### 📊 EDA (Exploratory Data Analysis)
Get intimate with your data.
*   **Univariate**: Look at one column at a time. Histograms, box plots, the works.
*   **Bivariate**: Compare two columns. Scatter plots, correlation heatmaps.
*   **Contrast**: See how your data differs across categories.

### 🧑‍💻 SQL Lab (For the OGs)
If you speak SQL, this tab is for you.
*   Write standard SQL queries against your loaded dataframes.
*   We use DuckDB/Polars under the hood, so it's wicked fast.
*   Your dataframes are available as tables (e.g., `SELECT * FROM my_dataset`).

### 💳 Profiling (The Health Check)
Get a full report card on your dataset.
*   Missing values, unique counts, duplicates.
*   It's like a physical exam for your data.

## 🕹️ Workflow

1.  **Load**: Drop files in the sidebar.
2.  **Cook**: Use the Recipe tab to clean and transform.
3.  **Check**: pop over to EDA/Profiling to make sure you didn't mess up.
4.  **Export**: Download the result and flex on your colleagues.
