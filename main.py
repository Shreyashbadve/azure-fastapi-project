from fastapi import FastAPI, UploadFile, File, HTTPException
from azure.storage.blob import BlobServiceClient
import os
import pyodbc

app = FastAPI()

# -----------------------------
# Azure SQL Configuration
# -----------------------------

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# -----------------------------
# Azure Blob Storage
# -----------------------------

AZURE_STORAGE_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

CONTAINER_NAME = "learning-data"

if AZURE_STORAGE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )
    container_client = blob_service_client.get_container_client(
        CONTAINER_NAME
    )
else:
    blob_service_client = None
    container_client = None


# -----------------------------
# Database Connection
# -----------------------------

def get_connection():
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)


# -----------------------------
# Home
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "FastAPI is running on Azure",
        "database": "Azure SQL",
        "storage": "Azure Blob Storage"
    }


# -----------------------------
# Health Check
# -----------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# -----------------------------
# Get Employees
# -----------------------------

@app.get("/employees")
def get_employees():

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, department, salary FROM employees"
        )

        rows = cursor.fetchall()

        employees = []

        for row in rows:
            employees.append({
                "id": row.id,
                "name": row.name,
                "department": row.department,
                "salary": row.salary
            })

        cursor.close()
        connection.close()

        return {
            "employees": employees
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------
# Upload File to Blob Storage
# -----------------------------

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):

    if container_client is None:
        raise HTTPException(
            status_code=500,
            detail="Azure Storage is not configured"
        )

    try:
        blob_client = container_client.get_blob_client(file.filename)

        contents = await file.read()

        blob_client.upload_blob(
            contents,
            overwrite=True
        )

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "container": CONTAINER_NAME
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------
# List Files
# -----------------------------

@app.get("/files")
def list_files():

    if container_client is None:
        raise HTTPException(
            status_code=500,
            detail="Azure Storage is not configured"
        )

    try:
        files = []

        for blob in container_client.list_blobs():
            files.append({
                "name": blob.name,
                "size": blob.size
            })

        return {
            "files": files
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


import os

@app.get("/config-check")
def config_check():
    return {
        "storage_configured": bool(
            os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        ),
        "db_configured": bool(
            os.getenv("DB_SERVER")
        )
    }