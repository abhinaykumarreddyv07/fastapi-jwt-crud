from fastapi import FastAPI, Depends, HTTPException, Query, Body
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from typing import Optional, List, Union
from datetime import timedelta

from models import Employee, User
from database import engine, Base, get_db
from auth import (
    get_current_user,
    get_current_admin_user,
    get_current_manager_user,
    authenticate_user,
    create_access_token,
    get_password_hash,
)

from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List

# ------------------ APP INIT ------------------
app = FastAPI()
Base.metadata.create_all(bind=engine)

# ------------------ SCHEMAS ------------------
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "employee"

class Token(BaseModel):
    access_token: str
    token_type: str

class EmployeeSchema(BaseModel):
    name: str
    salary: int
    department: str
    joindate: Optional[str] = None
    profile_pic: Optional[str] = None

class EmployeeUpdateSchema(BaseModel):
    name: Optional[str] = None
    salary: Optional[int] = None
    department: Optional[str] = None
    joindate: Optional[str] = None
    profile_pic: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    sr_no: int
    name: str
    salary: int
    department: str
    joindate: Optional[str] = None
    profile_pic: Optional[str] = None

    class Config:
        orm_mode = True

class BulkEmployeeSchema(BaseModel):
    employees: List[EmployeeSchema]

# ------------------ HELPERS ------------------
def response_message(status: str, message: str = None, data: str = None):
    return {"status": status, "message": message, "data": data}

def reset_serial_numbers(db: Session):
    employees = db.query(Employee).order_by(Employee.id).all()
    for idx, emp in enumerate(employees, start=1):
        emp.sr_no = idx
    db.commit()

# ------------------ AUTH ROUTES ------------------
@app.post("/register")
def register(
    users: Union[UserCreate, List[UserCreate]] = Body(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    # ---------------- BULK REGISTRATION ----------------
    if isinstance(users, list):
        if len(users) == 0:
            raise HTTPException(status_code=400, detail="Empty user list")

        inserted = []
        skipped = []

        for user in users:
            existing = db.query(User).filter(User.username == user.username).first()
            if existing:
                skipped.append({"username": user.username, "reason": "Duplicate"})
                continue

            if user.role not in ["admin", "manager", "employee"]:
                skipped.append({"username": user.username, "reason": "Invalid role"})
                continue

            hashed_pw = get_password_hash(user.password)
            new_user = User(username=user.username, password=hashed_pw, role=user.role)
            db.add(new_user)
            inserted.append({"username": user.username, "role": user.role})

        db.commit()
        return {
            "status": "success",
            "inserted_count": len(inserted),
            "skipped_count": len(skipped),
            "inserted": inserted,
            "skipped": skipped
        }

    # ---------------- SINGLE USER REGISTRATION ----------------
    existing = db.query(User).filter(User.username == users.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    if users.role not in ["admin", "manager", "employee"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    hashed_pw = get_password_hash(users.password)
    new_user = User(username=users.username, password=hashed_pw, role=users.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "status": "success",
        "username": new_user.username,
        "role": new_user.role
    }

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------ EMPLOYEE CRUD ------------------

# Create employee (Admin only)
@app.post("/employees")
def create_employees_bulk(
    employees: Union[EmployeeSchema, List[EmployeeSchema]] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin_user)  # Only admins can bulk insert
):
    # Convert single employee to list
    if isinstance(employees, EmployeeSchema):
        employees = [employees]

    # Check for duplicates (name + department)
    duplicate_entries = []
    for emp in employees:
        existing = db.query(Employee).filter(
            Employee.name == emp.name,
            Employee.department == emp.department
        ).first()
        if existing:
            duplicate_entries.append(f"{emp.name} ({emp.department})")

    if duplicate_entries:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate employee(s) found in same department: {', '.join(duplicate_entries)}"
        )

    # Insert all if no duplicates
    inserted = []
    for emp in employees:
        new_emp = Employee(
            sr_no=0,  # will reset later
            name=emp.name,
            salary=emp.salary,
            department=emp.department,
            joindate=emp.joindate,
            profile_pic=emp.profile_pic
        )
        db.add(new_emp)
        inserted.append({"name": emp.name, "department": emp.department, "salary": emp.salary})

    db.commit()

    # Reset serial numbers
    all_emps = db.query(Employee).order_by(Employee.id).all()
    for idx, emp in enumerate(all_emps, start=1):
        emp.sr_no = idx
    db.commit()

    return {
        "status": "success",
        "inserted_count": len(inserted),
        "inserted": inserted
    }

# Read employees
@app.get("/employees", response_model=List[EmployeeResponse])
def get_employees(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    department: str | None = Query(None, description="Filter by department"),
    min_salary: int | None = Query(None, description="Filter by minimum salary"),
    max_salary: int | None = Query(None, description="Filter by maximum salary"),
    search: str | None = Query(None, description="Search by name"),
    sort_by: str = Query("id", description="Sort by column (id, name, salary, joindate)"),
    order: str = Query("asc", description="Order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Employee)

    # Filters
    if department:
        query = query.filter(Employee.department == department)
    if min_salary is not None:
        query = query.filter(Employee.salary >= min_salary)
    if max_salary is not None:
        query = query.filter(Employee.salary <= max_salary)

    # Search
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(Employee.name.ilike(search_pattern))

    # Sorting
    sort_column = getattr(Employee, sort_by, None)
    if not sort_column:
        raise HTTPException(status_code=400, detail="Invalid sort column")
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    employees = query.offset((page - 1) * size).limit(size).all()
    return employees

# Read single employee (Everyone)
@app.get("/employees/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

# Update employee (Manager or Admin)
@app.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, emp_update: EmployeeUpdateSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_manager_user)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in emp_update.dict(exclude_unset=True).items():
        setattr(emp, field, value)

    db.commit()
    db.refresh(emp)
    return emp

# Delete employee (Admin only)
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin_user)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(emp)
    db.commit()
    reset_serial_numbers(db)
    return response_message("success", "Employee deleted", {"deleted_id": emp_id})
