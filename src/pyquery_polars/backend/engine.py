from typing import Callable, Any, Dict, List, Optional, Union, Type
import polars as pl
import threading
import uuid
import time
import os
from pydantic import BaseModel

# Import Utils
from pyquery_polars.backend.utils.io import get_files_from_path, load_lazy_frame, load_from_sql, load_from_api, export_worker
from pyquery_polars.backend.io_plugins.standard import ALL_LOADERS, ALL_EXPORTERS
from pyquery_polars.core.models import RecipeStep, StepMetadata, JobInfo, PluginDef, TransformContext
from pyquery_polars.core.registry import StepRegistry, StepDefinition

# Import Params (still needed for registration)
from pyquery_polars.core.params import (
    SelectColsParams, DropColsParams, RenameColParams, KeepColsParams, AddColParams, CleanCastParams,
    FilterRowsParams, SortRowsParams, DeduplicateParams, SampleParams,
    JoinDatasetParams, AggregateParams, WindowFuncParams, ReshapeParams,
    FillNullsParams, RegexExtractParams, TimeBinParams, RollingAggParams, NumericBinParams,
    StringCaseParams, StringReplaceParams, MathOpParams, DateExtractParams,
    DropNullsParams, TextSliceParams, TextLengthParams,
    CumulativeParams, RankParams, DiffParams,
    MathSciParams, ClipParams, DateOffsetParams, DateDiffParams
)

# Import Transforms (Backend Logic)
from pyquery_polars.backend.transforms.columns import (
    select_cols_func, drop_cols_func, rename_col_func,
    keep_cols_func, add_col_func, clean_cast_func
)
from pyquery_polars.backend.transforms.rows import (
    filter_rows_func, sort_rows_func, deduplicate_func, sample_func
)
from pyquery_polars.backend.transforms.combine import (
    join_dataset_func, aggregate_func, window_func_func, reshape_func
)
from pyquery_polars.backend.transforms.cleaning import (
    fill_nulls_func, regex_extract_func, string_case_func, string_replace_func,
    drop_nulls_func, text_slice_func, text_length_func
)
from pyquery_polars.backend.transforms.analytics import (
    time_bin_func, rolling_agg_func, numeric_bin_func, math_op_func, date_extract_func,
    cumulative_func, rank_func, diff_func
)
from pyquery_polars.backend.transforms.scientific import (
    math_sci_func, clip_func, date_offset_func, date_diff_func
)

# Import Transforms (Backend Logic)
from pyquery_polars.backend.transforms.columns import (
    select_cols_func, drop_cols_func, rename_col_func,
    keep_cols_func, add_col_func, clean_cast_func
)
from pyquery_polars.backend.transforms.rows import (
    filter_rows_func, sort_rows_func, deduplicate_func, sample_func
)
from pyquery_polars.backend.transforms.combine import (
    join_dataset_func, aggregate_func, window_func_func, reshape_func
)
from pyquery_polars.backend.transforms.cleaning import (
    fill_nulls_func, regex_extract_func, string_case_func, string_replace_func,
    drop_nulls_func, text_slice_func, text_length_func
)
from pyquery_polars.backend.transforms.analytics import (
    time_bin_func, rolling_agg_func, numeric_bin_func, math_op_func, date_extract_func,
    cumulative_func, rank_func, diff_func
)
from pyquery_polars.backend.transforms.scientific import (
    math_sci_func, clip_func, date_offset_func, date_diff_func
)


class PyQueryEngine:
    def __init__(self):
        self._datasets: Dict[str, pl.LazyFrame] = {}  # In-memory storage
        self._jobs: Dict[str, JobInfo] = {}

        # IO Plugins
        self._loaders: Dict[str, PluginDef] = {}
        self._exporters: Dict[str, PluginDef] = {}

        self._init_registry()
        self._register_io_defaults()

    def _init_registry(self):
        # Bootstrap the StepRegistry
        if StepRegistry.get_supported_steps():
            return

        R = StepRegistry

        # Columns
        R.register("select_cols", StepMetadata(label="Select Columns",
                   group="Columns"), SelectColsParams, select_cols_func)
        R.register("drop_cols", StepMetadata(label="Drop Columns",
                   group="Columns"), DropColsParams, drop_cols_func)
        R.register("rename_col", StepMetadata(label="Rename Column",
                   group="Columns"), RenameColParams, rename_col_func)
        R.register("keep_cols", StepMetadata(label="Keep Specific (Finalize)",
                   group="Columns"), KeepColsParams, keep_cols_func)
        R.register("add_col", StepMetadata(label="Add New Column",
                   group="Columns"), AddColParams, add_col_func)
        R.register("clean_cast", StepMetadata(label="Clean / Cast Types",
                   group="Columns"), CleanCastParams, clean_cast_func)

        # Rows
        R.register("filter_rows", StepMetadata(label="Filter Rows", group="Rows"),
                   FilterRowsParams, filter_rows_func)
        R.register("sort_rows", StepMetadata(label="Sort Rows", group="Rows"),
                   SortRowsParams, sort_rows_func)
        R.register("deduplicate", StepMetadata(label="Deduplicate", group="Rows"),
                   DeduplicateParams, deduplicate_func)
        R.register("sample", StepMetadata(label="Sample Data",
                   group="Rows"), SampleParams, sample_func)

        # Combine
        R.register("join_dataset", StepMetadata(label="Join Dataset", group="Combine"),
                   JoinDatasetParams, join_dataset_func)
        R.register("aggregate", StepMetadata(label="Group By (Aggregate)",
                   group="Combine"), AggregateParams, aggregate_func)
        R.register("window_func", StepMetadata(label="Window Function",
                   group="Combine"), WindowFuncParams, window_func_func)
        R.register("reshape", StepMetadata(label="Reshape (Pivot/Melt)",
                   group="Combine"), ReshapeParams, reshape_func)

        # Clean
        R.register("fill_nulls", StepMetadata(label="Fill NULLs", group="Clean"),
                   FillNullsParams, fill_nulls_func)
        R.register("drop_nulls", StepMetadata(label="Drop NULL Rows",
                   group="Clean"), DropNullsParams, drop_nulls_func)
        R.register("regex_extract", StepMetadata(label="Regex Extract", group="Clean"),
                   RegexExtractParams, regex_extract_func)
        R.register("text_slice", StepMetadata(label="Text Slice (Substring)",
                   group="Clean"), TextSliceParams, text_slice_func)
        R.register("text_length", StepMetadata(label="Text Length", group="Clean"),
                   TextLengthParams, text_length_func)
        R.register("string_case", StepMetadata(label="String Case/Trim",
                   group="Clean"), StringCaseParams, string_case_func)
        R.register("string_replace", StepMetadata(label="String Replace", group="Clean"),
                   StringReplaceParams, string_replace_func)

        # Analytics
        R.register("time_bin", StepMetadata(label="Time Truncate (Bin)",
                   group="Analytics"), TimeBinParams, time_bin_func)
        R.register("rolling_agg", StepMetadata(label="Rolling Aggregate",
                   group="Analytics"), RollingAggParams, rolling_agg_func)
        R.register("numeric_bin", StepMetadata(label="Numeric Binning",
                   group="Analytics"), NumericBinParams, numeric_bin_func)
        R.register("cumulative", StepMetadata(label="Cumulative (Running)",
                   group="Analytics"), CumulativeParams, cumulative_func)
        R.register("rank", StepMetadata(label="Ranking",
                   group="Analytics"), RankParams, rank_func)
        R.register("diff", StepMetadata(label="Pct Change / Diff",
                   group="Analytics"), DiffParams, diff_func)

        # Math & Date
        R.register("math_op", StepMetadata(label="Math Operation",
                   group="Math & Date"), MathOpParams, math_op_func)
        R.register("math_sci", StepMetadata(label="Scientific Math",
                   group="Math & Date"), MathSciParams, math_sci_func)
        R.register("clip", StepMetadata(label="Clip / Clamp Values",
                   group="Math & Date"), ClipParams, clip_func)

        R.register("date_extract", StepMetadata(label="Date Extraction", group="Math & Date"),
                   DateExtractParams, date_extract_func)
        R.register("date_offset", StepMetadata(label="Date Offset (Add/Sub)",
                   group="Math & Date"), DateOffsetParams, date_offset_func)
        R.register("date_diff", StepMetadata(label="Date Duration (Diff)",
                   group="Math & Date"), DateDiffParams, date_diff_func)

    def _register_io_defaults(self):
        for l in ALL_LOADERS:
            self._loaders[l.name] = l
        for e in ALL_EXPORTERS:
            self._exporters[e.name] = e

    def get_supported_steps(self) -> List[str]:
        return StepRegistry.get_supported_steps()

    # ==========================
    # DATASET MANAGEMENT
    # ==========================
    def add_dataset(self, name: str, lf: pl.LazyFrame):
        self._datasets[name] = lf

    def remove_dataset(self, name: str):
        if name in self._datasets:
            del self._datasets[name]

    def get_dataset(self, name: str) -> Optional[pl.LazyFrame]:
        return self._datasets.get(name)

    def get_dataset_names(self) -> List[str]:
        return list(self._datasets.keys())

    def get_dataset_schema(self, name: str) -> Optional[pl.Schema]:
        lf = self.get_dataset(name)
        if lf is None:
            return None
        try:
            return lf.collect_schema()
        except:
            return None

    def get_transformed_schema(self, name: str, recipe: List[Union[dict, RecipeStep]]) -> Optional[pl.Schema]:
        base_lf = self.get_dataset(name)
        if base_lf is None:
            return None
        try:
            # Re-use apply_recipe logic
            transformed_lf = self.apply_recipe(base_lf, recipe)
            return transformed_lf.collect_schema()
        except:
            return None

    # ==========================
    # EXPORT JOBS
    # ==========================
    def get_loaders(self) -> List[PluginDef]:
        return list(self._loaders.values())

    def get_exporters(self) -> List[PluginDef]:
        return list(self._exporters.values())

    def run_loader(self, loader_name: str, params: Union[Dict[str, Any], BaseModel]) -> Optional[pl.LazyFrame]:
        loader = self._loaders.get(loader_name)
        if not loader:
            return None

        # Guard against missing function
        if not loader.func:
            return None

        try:
            if loader.params_model:
                if isinstance(params, BaseModel):
                    validated_params = params
                else:
                    validated_params = loader.params_model.model_validate(
                        params)
                return loader.func(validated_params)
            else:
                return loader.func(params)
        except Exception as e:
            print(f"Loader Error: {e}")
            return None

    def start_export_job(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]], exporter_name: str, params: Union[Dict[str, Any], BaseModel]) -> str:
        job_id = str(uuid.uuid4())
        exporter = self._exporters.get(exporter_name)
        if not exporter:
            raise ValueError(f"Unknown exporter: {exporter_name}")

        if not exporter.func:
            raise ValueError(f"Exporter {exporter_name} has no function")

        validated_params = params
        if exporter.params_model:
            try:
                if not isinstance(params, BaseModel):
                    validated_params = exporter.params_model.model_validate(
                        params)
            except Exception as e:
                raise ValueError(f"Invalid export configuration: {e}")

        # Safe Path extraction
        path = "unknown"
        if hasattr(validated_params, 'path'):
            path = getattr(validated_params, 'path')
        elif isinstance(params, dict):
            path = params.get('path', 'unknown')

        job_info = JobInfo(
            job_id=job_id,
            status="RUNNING",
            file=path
        )
        self._jobs[job_id] = job_info

        t = threading.Thread(target=self._internal_export_worker, args=(
            job_id, dataset_name, recipe, exporter_name, validated_params))
        t.start()
        return job_id

    def _internal_export_worker(self, job_id, dataset_name, recipe, exporter_name, params):
        start_time = time.time()
        try:
            base_lf = self.get_dataset(dataset_name)
            if base_lf is None:
                raise ValueError("Dataset not found")

            final_lf = self.apply_recipe(base_lf, recipe)

            exporter = self._exporters.get(exporter_name)
            if exporter and exporter.func:
                exporter.func(final_lf, params)

            end_time = time.time()
            duration = end_time - start_time

            info = self._jobs[job_id]
            info.duration = duration
            info.status = "COMPLETED"

            # Size check
            path = None
            if hasattr(params, 'path'):
                path = getattr(params, 'path')
            elif isinstance(params, dict):
                path = params.get('path')

            if path and os.path.exists(path):
                size_bytes = os.path.getsize(path)
                info.size_str = f"{size_bytes / 1024 / 1024:.2f} MB"

        except Exception as e:
            if job_id in self._jobs:
                self._jobs[job_id].duration = time.time() - start_time
                self._jobs[job_id].status = "FAILED"
                self._jobs[job_id].error = str(e)

    def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        return self._jobs.get(job_id)

    # ==========================
    # TRANSFORMATION ENGINE
    # ==========================
    def apply_step(self, lf: pl.LazyFrame, step: RecipeStep, context: Optional[TransformContext] = None) -> pl.LazyFrame:
        step_type = step.type
        definition = StepRegistry.get(step_type)
        if not definition:
            raise ValueError(f"Unknown step type: {step_type}")

        try:
            if isinstance(step.params, BaseModel):
                validated_params = step.params
            else:
                validated_params = definition.params_model.model_validate(
                    step.params)
        except Exception as e:
            raise ValueError(f"Parameters invalid for step {step_type}: {e}")

        if context is None:
            context = TransformContext(datasets=self._datasets)

        return definition.backend_func(lf, validated_params, context)

    def apply_recipe(self, lf: pl.LazyFrame, recipe: List[Union[dict, RecipeStep]]) -> pl.LazyFrame:
        current_lf = lf
        context = TransformContext(datasets=self._datasets)

        for step in recipe:
            if isinstance(step, dict):
                if 'type' not in step:
                    continue
                step_obj = RecipeStep(**step)
            else:
                step_obj = step

            current_lf = self.apply_step(current_lf, step_obj, context=context)

        return current_lf

    def get_preview(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]], limit: int = 50) -> Optional[pl.DataFrame]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None

# OPTIMIZATION: Sample logic
        # Apply limit BEFORE transformations for performance
        # This means sorts/aggs are only on the sample, which is the requested trade-off.
        sampled_lf = base_lf.limit(limit)

        # No try/catch wrapper here - let errors propagate to UI
        transformed_lf = self.apply_recipe(sampled_lf, recipe)
        return transformed_lf.collect()

    def get_profile(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]]) -> Optional[Dict[str, Any]]:
        """
        Generates a statistical profile of the dataset after applying the recipe.
        """
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None

        try:
            lf = self.apply_recipe(base_lf, recipe)

            # 1. Collect Schema/Shape
            schema = lf.collect_schema()
            # To get row count
            # Let's verify on 10k rows for interactivity.

            sample_df = lf.limit(10000).collect()

            # 2. Stats
            # shape
            rows, cols = sample_df.shape

            # nulls
            null_counts = {c: sample_df[c].null_count()
                           for c in sample_df.columns}

            # dtypes logic
            dtypes = {c: str(sample_df[c].dtype) for c in sample_df.columns}

            # summary (describe)
            summary = sample_df.describe().to_pandas()

            return {
                "sample": sample_df,
                "shape": (rows, cols),
                "nulls": null_counts,
                "dtypes": dtypes,
                "summary": summary
            }

        except Exception as e:
            return {"error": str(e)}
