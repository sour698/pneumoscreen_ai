from fastapi import FastAPI
from routes import predict, patients, reports

app = FastAPI(title="Clinical AI Platform")

app.include_router(predict.router)
app.include_router(patients.router)
app.include_router(reports.router)

@app.get("/")
def home():
    return {"status": "API running"}