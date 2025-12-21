from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pyquery_polars.api.routes import meta, datasets, recipes

app = FastAPI(
    title="PyQuery Engine API",
    description="Headless ETL Engine for High-Performance Data Processing",
    version="1.0.0"
)

# CORS (Allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route Registration
app.include_router(meta.router, prefix="/meta", tags=["Metadata"])
app.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
app.include_router(recipes.router, prefix="/recipes", tags=["Recipes"])


@app.get("/")
def root():
    return {"status": "ok", "service": "PyQuery Engine"}
