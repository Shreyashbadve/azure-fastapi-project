import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

app = FastAPI(
    title="Azure FastAPI Employee API",
    description="FastAPI application connected to Azure SQL Database",
    version="1.0.0"
)


# Azure SQL connection
connection_url = URL.create(
    "mssql+pyodbc",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_SERVER"),
    database=os.getenv("DB_NAME"),
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "Encrypt": "yes",
        "TrustServerCertificate": "no",
    },
)

engine = create_engine(connection_url)


# Employee request model
class Employee(BaseModel):
    id: int
    name: str
    department: str
    salary: int


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "FastAPI is running on Azure"
    }


# Health check endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Get all employees
@app.get("/employees")
def get_employees():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, name, department, salary
                    FROM employees
                    ORDER BY id
                """)
            )

            employees = [
                dict(row._mapping)
                for row in result
            ]

        return {
            "employees": employees
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# Create a new employee
@app.post("/employees", status_code=201)
def create_employee(employee: Employee):
    try:
        with engine.begin() as connection:

            # Check whether ID already exists
            existing = connection.execute(
                text("""
                    SELECT id
                    FROM employees
                    WHERE id = :id
                """),
                {"id": employee.id}
            ).fetchone()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Employee with this ID already exists"
                )

            connection.execute(
                text("""
                    INSERT INTO employees
                    (id, name, department, salary)
                    VALUES
                    (:id, :name, :department, :salary)
                """),
                employee.model_dump()
            )

        return {
            "message": "Employee created successfully",
            "employee": employee.model_dump()
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# Get employee by ID
@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, name, department, salary
                    FROM employees
                    WHERE id = :id
                """),
                {"id": employee_id}
            ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )

        return {
            "employee": dict(result._mapping)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )