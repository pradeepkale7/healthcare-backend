from fastapi import FastAPI
from app.core.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import db_data_insert
from app.api.routes import file_report
from app.api.routes import file_import
from app.api.routes import file_list
from app.api.routes import analytic_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",],  # Frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    print(Base.metadata.tables.keys())
    Base.metadata.create_all(bind=engine)
    
app.include_router(file_import.router, prefix="/resource" ,tags=["File Import"])
app.include_router(db_data_insert.router, prefix="/resource", tags=["Data Insertion "])
app.include_router(file_report.router, prefix="/resource", tags=["File Report Generation"])
app.include_router(file_list.router, prefix="/resource", tags=["File List Generation"])
app.include_router(analytic_report.router, prefix="/resource", tags=["Analytics Report Generation"])


@app.get("/")
def root():
    return {"message": "API is running"}
