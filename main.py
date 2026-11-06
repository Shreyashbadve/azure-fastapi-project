from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI is running on Azure"}

@app.get("/health")
def health():
    return {"status": "healthy"}