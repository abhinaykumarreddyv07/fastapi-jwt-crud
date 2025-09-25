FastAPI Employee Management API

This project is a simple **FastAPI + MySQL** application that performs full **CRUD (Create, Read, Update, Delete)** operations on an employee database.  
It is designed to demonstrate how to connect FastAPI with a MySQL backend using **SQLAlchemy ORM**.

## Features
- Add a new employee (with duplicate checks).
- Fetch all employees or a single employee by ID.
- Update employee details (with duplicate prevention).
- Delete an employee.
- Auto-managed **serial numbers** (separate from ID).
- Employee profile pictures stored as paths (can be displayed in API responses).

## This project currently has two implementations:

1. **FastAPI + MySQL (main.py)**  
   - Recommended production-ready version  
   - Uses SQLAlchemy ORM and MySQL database  

2. **FastAPI + Local JSON (main.py (starting code which is in comment from loc 1 - 66) )**  
   - Simple beginner-friendly version  
   - Reads and writes employee data from a local `data.json` file  
   - Good for learning FastAPI basics without setting up a database

## Tech Stack
- **Python 3.10+**
- **FastAPI**
- **SQLAlchemy**
- **MySQL**
- **Pydantic** (for request validation)
- **Uvicorn** (for running the server)
