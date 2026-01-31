from typing import Optional

import os
import shutil
import requests
import polars as pl
from pydantic import BaseModel

from pyquery_polars.backend.io.loaders.base import BaseLoader, LoaderOutput
from pyquery_polars.core.io import ApiLoaderParams


class APILoaderOutput(BaseModel):
    url: str
    dataset_alias: str


class APILoader(BaseLoader[ApiLoaderParams, APILoaderOutput]):
    """
    Loader for importing JSON data from REST APIs.
    """

    def run(self) -> Optional[LoaderOutput[APILoaderOutput]]:
        url = self.params.url
        dataset_alias = self.params.alias
        meta = APILoaderOutput(url=url, dataset_alias=dataset_alias)
        try:
            base_name = dataset_alias if dataset_alias else "api_dump"
            staging_dir = self.staging.create_unique_staging_folder(base_name)

            file_name = "api_data.json"
            file_path = os.path.join(staging_dir, file_name)

            # Stream download (low memory usage)
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

            # Return LazyFrame from disk
            lf = pl.read_json(file_path).lazy()
            return LoaderOutput(lf=lf, meta=meta)
        except Exception as e:
            print(f"API Error: {e}")
            return None
