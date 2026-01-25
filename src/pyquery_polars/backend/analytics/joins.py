
from typing import List, Dict, Any, Optional

import polars as pl


class JoinAnalyzer:
    @staticmethod
    def analyze_overlap(l_df: Optional[pl.DataFrame],
                        r_df: Optional[pl.DataFrame],
                        left_on: List[str],
                        right_on: List[str],
                        left_name: str = "Left dataset",
                        right_name: str = "Right dataset") -> Dict[str, Any]:
        """
        Analyzes the overlap between two Polars DataFrames (eager execution) 
        based on join keys. Returns counts and match statistics.
        """
        if l_df is None:
            return {"error": f"{left_name} preview failed."}
        if r_df is None:
            return {"error": f"{right_name} preview failed."}

        try:
            l_count = len(l_df)
            r_count = len(r_df)

            if l_count == 0 or r_count == 0:
                return {"l_count": l_count, "r_count": r_count, "match_count": 0}

            # Join (Eager)
            match_count = len(l_df.join(r_df, left_on=left_on,
                              right_on=right_on, how="inner"))

            return {
                "l_count": l_count,
                "r_count": r_count,
                "match_count": match_count
            }
        except Exception as e:
            return {"error": str(e)}
