import streamlit as st
import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt
from typing import cast, Any
from pyquery_polars.backend.engine import PyQueryEngine

def apply_custom_theme():
    """Applies a dark/premium theme to Seaborn/Matplotlib."""
    sns.set_theme(style="darkgrid", rc={
        "axes.facecolor": "#0e1117", # Streamlit dark bg
        "figure.facecolor": "#0e1117",
        "grid.color": "#262730",
        "text.color": "#fafafa",
        "axes.labelcolor": "#fafafa",
        "xtick.color": "#fafafa",
        "ytick.color": "#fafafa",
        "axes.edgecolor": "#262730"
    })
    # Vibrant Palette
    sns.set_palette("bright") 

def render_eda_tab():
    st.subheader("📊 Exploratory Data Analysis")

    # 1. Get Engine & Active Dataset
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        st.error("Engine not initialized.")
        return

    active_ds = st.session_state.get('active_base_dataset')
    if not active_ds:
        st.info("Please select a dataset in the Sidebar to analyze.")
        return

    # 2. Prepare Data (Sampled for Performance)
    LIMIT_ROWS = 5000
    
    with st.spinner(f"Preparing EDA for '{active_ds}' (Top {LIMIT_ROWS} rows)..."):
        try:
            project_recipes = st.session_state.get('all_recipes', {}) or {}
            current_recipe = project_recipes.get(active_ds, [])
            
            base_lf = engine.get_dataset(active_ds)
            if base_lf is None:
                st.error("Dataset not found.")
                return

            transformed_lf = engine.apply_recipe(base_lf, current_recipe, project_recipes)
            
            # Eager Pandas DF for Seaborn
            # We must convert to Pandas as Seaborn expects it
            df = transformed_lf.head(LIMIT_ROWS).collect().to_pandas()
            
            # Identify columns
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns.tolist()

        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    # Apply Theme
    apply_custom_theme()

    st.caption(f"Analyzing '{active_ds}' • Shape: {df.shape}")

    # --- TABS ---
    tab_overview, tab_uni, tab_bi, tab_multi = st.tabs([
        "📋 Overview", "📊 Univariate", "📈 Bivariate", "🕸️ Multivariate"
    ])

    # 1. OVERVIEW
    with tab_overview:
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows (Sampled)", df.shape[0])
        c1.metric("Columns", df.shape[1])
        c2.metric("Numerical Features", len(num_cols))
        c2.metric("Categorical Features", len(cat_cols))
        c3.metric("Total Missing Cells", df.isna().sum().sum())
        
        st.divider()
        st.write("###### Data Preview")
        st.dataframe(df.head(10), width="stretch")
        
        st.write("###### Descriptive Statistics")
        st.dataframe(df.describe(include='all').astype(str).T, width="stretch")
        
        st.write("###### Missing Value Heatmap")
        if df.isna().sum().sum() > 0:
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.heatmap(df.isna(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)
            st.pyplot(fig, transparent=True)
        else:
            st.success("No missing values found in sample!")

    # 2. UNIVARIATE
    with tab_uni:
        st.write("#### Single Variable Distribution")
        target_col = st.selectbox("Select Column", df.columns, key="eda_uni_col")
        
        if target_col in num_cols:
            plot_type = st.radio("Plot Type", ["Histogram & KDE", "Box Plot", "Violin Plot"], horizontal=True)
            fig, ax = plt.subplots(figsize=(10, 5))
            
            if plot_type == "Histogram & KDE":
                sns.histplot(data=df, x=target_col, kde=True, ax=ax, color='cyan')
            elif plot_type == "Box Plot":
                sns.boxplot(data=df, x=target_col, ax=ax, color='cyan')
            elif plot_type == "Violin Plot":
                sns.violinplot(data=df, x=target_col, ax=ax, color='cyan')
                
            st.pyplot(fig, transparent=True)
            
        elif target_col in cat_cols:
            plot_type = st.radio("Plot Type", ["Count Plot", "Pie Chart"], horizontal=True)
            
            if plot_type == "Count Plot":
                fig, ax = plt.subplots(figsize=(10, 5))
                # Limit to top 20 categories to avoid clutter
                top_cats = df[target_col].value_counts().nlargest(20).index
                filter_df = df[df[target_col].isin(top_cats)]
                sns.countplot(data=filter_df, y=target_col, order=top_cats, ax=ax, palette='bright', hue=target_col, legend=False)
                st.pyplot(fig, transparent=True)
                if len(df[target_col].unique()) > 20:
                     st.warning("Showing top 20 categories only.")
            
            else: # Pie
                counts = df[target_col].value_counts().nlargest(10)
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.pie(counts, labels=counts.index.astype(str).tolist(), autopct='%1.1f%%', colors=sns.color_palette('bright'))
                st.pyplot(fig, transparent=True)

    # 3. BIVARIATE
    with tab_bi:
        st.write("#### Relationship Analysis")
        
        mode = st.radio("Compare", ["Numerical vs Numerical", "Numerical vs Categorical", "Correlation Matrix"], horizontal=True)
        
        if mode == "Numerical vs Numerical":
            c1, c2, c3, c4 = st.columns(4)
            x_ax = c1.selectbox("X Axis", num_cols, index=0 if len(num_cols)>0 else None, key="bi_num_x")
            y_ax = c2.selectbox("Y Axis", num_cols, index=1 if len(num_cols)>1 else 0, key="bi_num_y")
            hue = c3.selectbox("Color By (Cat)", ["None"] + cat_cols, key="bi_hue")
            kind = c4.selectbox("Plot Kind", ["Scatter", "Reg Plot", "Hexbin"], key="bi_kind")
            
            if x_ax and y_ax:
                fig = plt.figure(figsize=(10, 6))
                
                # Handling Hue logic
                hue_arg = hue if hue != "None" else None
                
                if kind == "Scatter":
                    if hue_arg:
                        sns.scatterplot(data=df, x=x_ax, y=y_ax, hue=hue_arg, palette='bright')
                    else:
                        sns.scatterplot(data=df, x=x_ax, y=y_ax, color='cyan')
                elif kind == "Reg Plot":
                    # Regplot supports hue but via FacetGrid usually, raw regplot is simpler
                    if hue_arg:
                        sns.lmplot(data=df, x=x_ax, y=y_ax, hue=hue_arg, height=6, aspect=1.5)
                        # sns.lmplot creates its own figure, so we handle differently
                        st.pyplot(plt.gcf(), transparent=True)
                        return # Exit early for lmplot
                    else:
                        sns.regplot(data=df, x=x_ax, y=y_ax, color='cyan')
                elif kind == "Hexbin":
                     plt.hexbin(df[x_ax], df[y_ax], gridsize=20, cmap='viridis')
                     plt.colorbar()

                if kind != "Reg Plot" or (kind == "Reg Plot" and not hue_arg):
                    st.pyplot(fig, transparent=True)

        elif mode == "Numerical vs Categorical":
            c1, c2, c3 = st.columns(3)
            cat_ax = c1.selectbox("Categorical (X)", cat_cols, key="bi_cat_x")
            num_ax = c2.selectbox("Numerical (Y)", num_cols, key="bi_cat_y")
            kind = c3.selectbox("Chart", ["Box Plot", "Violin Plot", "Strip Plot", "Bar Plot (Mean)"], key="bi_cat_kind")
            
            if cat_ax and num_ax:
                # Limit cats
                top_cats = df[cat_ax].value_counts().nlargest(15).index
                plot_df = df[df[cat_ax].isin(top_cats)]
                
                fig, ax = plt.subplots(figsize=(12, 6))
                
                if kind == "Box Plot":
                    sns.boxplot(data=plot_df, x=cat_ax, y=num_ax, palette='bright', ax=ax, order=top_cats, hue=cat_ax, legend=False)
                elif kind == "Violin Plot":
                    sns.violinplot(data=plot_df, x=cat_ax, y=num_ax, palette='bright', ax=ax, order=top_cats, hue=cat_ax, legend=False)
                elif kind == "Strip Plot":
                    sns.stripplot(data=plot_df, x=cat_ax, y=num_ax, palette='bright', ax=ax, order=top_cats, alpha=0.6, hue=cat_ax, legend=False)
                elif kind == "Bar Plot (Mean)":
                    sns.barplot(data=plot_df, x=cat_ax, y=num_ax, estimator='mean', palette='bright', ax=ax, order=top_cats, hue=cat_ax, legend=False)
                    
                plt.xticks(rotation=45)
                st.pyplot(fig, transparent=True)

        elif mode == "Correlation Matrix":
            if len(num_cols) > 1:
                fig, ax = plt.subplots(figsize=(10, 8))
                corr = df[num_cols].corr()
                mask = None
                # Optional: mask upper triangle
                # mask = np.triu(np.ones_like(corr, dtype=bool))
                sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', ax=ax, center=0)
                st.pyplot(fig, transparent=True)
            else:
                st.warning("Need at least 2 numerical columns.")

    # 4. MULTIVARIATE
    with tab_multi:
        st.write("#### Pairplot (Scatter Matrix)")
        
        # Options Config
        with st.expander("⚙️ Analysis Settings", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            chart_kind = c1.selectbox("Chart Kind", ["scatter", "kde", "hist", "reg"], index=0)
            diag_kind = c2.selectbox("Diagonal Kind", ["auto", "hist", "kde"], index=0)
            corner_plot = c3.checkbox("Corner Plot", value=True)
            hue_opt = c4.selectbox("Color By", ["None"] + cat_cols, key="pair_hue")

        # Column Selection (Numeric Only)
        sel_cols = st.multiselect(
            "Select Numerical Columns to Compare", 
            num_cols, 
            default=num_cols[:4] if len(num_cols) >=4 else num_cols[:2]
        )
        
        # Plot Trigger
        if st.checkbox("Generate Pairplot", value=False):
            if len(sel_cols) < 2:
                st.error("Select at least 2 columns.")
            else:
                with st.spinner("Rendering Complex Pairplot..."):
                    hue = hue_opt if hue_opt != "None" else None
                    
                    cols_to_plot = []
                    try:
                        # Prepare subset
                        cols_to_plot = list(set(sel_cols))
                        
                        # Add hue to dataframe if not in selection
                        needed_cols = set(cols_to_plot)
                        if hue: 
                            needed_cols.add(hue)
                        
                        plot_df = df[list(needed_cols)]
                        
                        g = sns.pairplot(
                            plot_df, 
                            vars=cols_to_plot, # Explicitly pass vars
                            hue=hue, 
                            palette='bright', 
                            corner=corner_plot,
                            kind=cast(Any, chart_kind),
                            diag_kind=cast(Any, diag_kind),
                            plot_kws={'s': 15, 'alpha': 0.7} if chart_kind == 'scatter' else {}
                        )
                        st.pyplot(g.fig, transparent=True)
                    except ValueError as ve:
                        st.error(f"Data Error: {ve}")
                        st.caption("Hint: Ensure selected columns are compatible with the chosen chart kind.")
                    except Exception as e:
                         st.error(f"Plot Error: {e}")
                         if chart_kind == 'scatter' and any(c in cat_cols for c in cols_to_plot):
                             st.warning("Tip: Scatter plots require numerical variables. Try using 'hist' kind or removing non-numeric columns.")
