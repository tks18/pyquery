from typing import Callable, Any, Dict, List, Optional
import polars as pl
import threading
import uuid
import time
import os

# Import Utils
from src.backend.utils.io import get_files_from_path, load_lazy_frame, load_from_sql, load_from_api, export_worker
from src.backend.io_plugins.standard import ALL_LOADERS, ALL_EXPORTERS

# Import Transforms
from src.backend.transforms.columns import (
    select_cols_func, drop_cols_func, rename_col_func, 
    keep_cols_func, add_col_func, clean_cast_func
)
from src.backend.transforms.rows import (
    filter_rows_func, sort_rows_func, deduplicate_func, sample_func
)
from src.backend.transforms.combine import (
    join_dataset_func, aggregate_func, window_func_func, reshape_func
)

class TransformDefinition:
    def __init__(
        self, 
        step_type: str, 
        func: Callable[[Any, Dict[str, Any]], Any],
        metadata: Dict[str, Any] = None
    ):
        self.step_type = step_type
        self.func = func
        self.metadata = metadata or {}

class PyQueryEngine:
    def __init__(self):
        self._transforms: Dict[str, TransformDefinition] = {}
        self._datasets: Dict[str, pl.LazyFrame] = {}  # In-memory storage of base datasets
        self._jobs: Dict[str, Dict[str, Any]] = {}
        
        # IO Plugins
        self._loaders: Dict[str, Any] = {}
        self._exporters: Dict[str, Any] = {}
        
        self._register_defaults()

    def _register_defaults(self):
        # Transfroms
        # Columns
        self.register_transform("select_cols", select_cols_func, {"label": "Select Columns", "group": "Columns"})
        self.register_transform("drop_cols", drop_cols_func, {"label": "Drop Columns", "group": "Columns"})
        self.register_transform("rename_col", rename_col_func, {"label": "Rename Column", "group": "Columns"})
        self.register_transform("keep_cols", keep_cols_func, {"label": "Keep Specific (Finalize)", "group": "Columns"})
        self.register_transform("add_col", add_col_func, {"label": "Add New Column", "group": "Columns"})
        self.register_transform("clean_cast", clean_cast_func, {"label": "Clean / Cast Types", "group": "Columns"})
        
        # Rows
        self.register_transform("filter_rows", filter_rows_func, {"label": "Filter Rows", "group": "Rows"})
        self.register_transform("sort_rows", sort_rows_func, {"label": "Sort Rows", "group": "Rows"})
        self.register_transform("deduplicate", deduplicate_func, {"label": "Deduplicate", "group": "Rows"})
        self.register_transform("sample", sample_func, {"label": "Sample Data", "group": "Rows"})
        
        # Combine
        self.register_transform("join_dataset", join_dataset_func, {"label": "Join Dataset", "group": "Combine"})
        self.register_transform("aggregate", aggregate_func, {"label": "Group By (Aggregate)", "group": "Combine"})
        self.register_transform("window_func", window_func_func, {"label": "Window Function", "group": "Combine"})
        self.register_transform("reshape", reshape_func, {"label": "Reshape (Pivot/Melt)", "group": "Combine"})

        # IO Plugins
        for l in ALL_LOADERS:
            self._loaders[l['name']] = l
        for e in ALL_EXPORTERS:
            self._exporters[e['name']] = e

    def register_transform(self, step_type: str, func: Callable, metadata: Dict = None):
        self._transforms[step_type] = TransformDefinition(step_type, func, metadata)

    def get_step_metadata(self, step_type: str) -> Dict[str, Any]:
        t = self._transforms.get(step_type)
        return t.metadata if t else {}

    def get_supported_steps(self) -> List[str]:
        return list(self._transforms.keys())

    # ==========================
    # DATASET MANAGEMENT (CRUD)
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
        
    def get_dataset_schema(self, name: str) -> Dict[str, Any]: # Simplified Schema
        lf = self.get_dataset(name)
        if lf is None: return {}
        try:
             # Lazy schema
             return lf.collect_schema()
        except:
             return {}

    # ==========================
    # EXPORT JOBS & I/O
    # ==========================
    
    def get_loaders(self) -> List[Dict]:
        return list(self._loaders.values())
        
    def get_exporters(self) -> List[Dict]:
        return list(self._exporters.values())

    def run_loader(self, loader_name: str, params: Dict[str, Any]) -> Optional[pl.LazyFrame]:
        loader = self._loaders.get(loader_name)
        if not loader: return None
        return loader['func'](params)

    def start_export_job(self, dataset_name: str, recipe: List[dict], exporter_name: str, params: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        
        # Get exporter definition
        exporter = self._exporters.get(exporter_name)
        if not exporter:
             raise ValueError(f"Unknown exporter: {exporter_name}")
             
        self._jobs[job_id] = {
            "status": "RUNNING",
            "start_time": time.time(),
            "file": params.get('path', 'unknown'),
            "type": "export"
        }
        
        t = threading.Thread(target=self._internal_export_worker, args=(job_id, dataset_name, recipe, exporter_name, params))
        t.start()
        return job_id

    def _internal_export_worker(self, job_id, dataset_name, recipe, exporter_name, params):
        try:
            base_lf = self.get_dataset(dataset_name)
            if base_lf is None:
                raise ValueError("Dataset not found")
            
            final_lf = self.apply_recipe(base_lf, recipe)
            
            # Use Exporter Plugin
            exporter = self._exporters.get(exporter_name)
            res = exporter['func'](final_lf, params)
            
            if res.get('status') != "Done":
                raise RuntimeError(res.get('status'))
            
            # success
            info = self._jobs[job_id]
            info["end_time"] = time.time()
            info["duration"] = info["end_time"] - info["start_time"]
            info["status"] = "COMPLETED"
            
            # Get file size logic (depends on path param existing)
            path = params.get('path')
            if path:
                try:
                    size_bytes = os.path.getsize(path)
                    # Convert to readable
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if size_bytes < 1024.0:
                            break
                        size_bytes /= 1024.0
                    info["size_str"] = f"{size_bytes:.2f} {unit}"
                except:
                    info["size_str"] = "Unknown"
            else:
                info["size_str"] = "N/A"
                
        except Exception as e:
            self._jobs[job_id]["status"] = "FAILED"
            self._jobs[job_id]["error"] = str(e)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        return self._jobs.get(job_id, {"status": "UNKNOWN"})

    # ==========================
    # TRANSFORMATION ENGINE
    # ==========================
    def apply_step(self, lf: pl.LazyFrame, step_type: str, params: dict, context: dict = None) -> pl.LazyFrame:
        t_def = self._transforms.get(step_type)
        if not t_def:
            raise ValueError(f"Unknown step type: {step_type}")
        
        # Inject datasets context if not provided, so join_dataset can work
        if context is None:
            context = {'datasets': self._datasets}
        else:
            if 'datasets' not in context:
                context['datasets'] = self._datasets

        try:
             return t_def.func(lf, params, context=context)
        except TypeError:
             return t_def.func(lf, params)

    def apply_recipe(self, lf: pl.LazyFrame, recipe: List[dict]) -> pl.LazyFrame:
        current_lf = lf
        context = {'datasets': self._datasets}
        for step in recipe:
            current_lf = self.apply_step(current_lf, step['type'], step['params'], context=context)
        return current_lf

    # ==========================
    # PREVIEW & PROFILING
    # ==========================
    def get_preview(self, dataset_name: str, recipe: List[dict], limit: int = 50) -> Optional[pl.DataFrame]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None: return None
        
        transformed_lf = self.apply_recipe(base_lf, recipe)
        try:
            return transformed_lf.limit(limit).collect()
        except Exception as e:
            raise e

    def get_profile(self, dataset_name: str, recipe: List[dict]) -> Optional[Dict[str, Any]]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None: return None
        
        transformed_lf = self.apply_recipe(base_lf, recipe)
        try:
            # Collect sample for profiling (limit 5000 for better stats than 1000, still fast)
            df = transformed_lf.limit(5000).collect()
            
            # Null counts per column
            null_counts = df.null_count().row(0, named=True)
            
            return {
                "summary": df.describe(),
                "dtypes": {col: str(dtype) for col, dtype in df.schema.items()},
                "nulls": null_counts,
                "shape": df.shape,
                "sample": df # Return small sample for visualization
            }
        except Exception as e:
            return {"error": str(e)}
