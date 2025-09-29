from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.orm import Session
from models import Employee, User
from database import engine, Base, get_db
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user, authenticate_user,create_access_token, get_password_hash
from datetime import timedelta
from auth import router as auth_router

app = FastAPI()
Base.metadata.create_all(bind=engine)
app.include_router(auth_router)

# --- SCHEMAS ---
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- REGISTER USER ---
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

# --- LOGIN (GET TOKEN) ---
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------- EMPLOYEE CRUD ----------------
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

def response_message(status: str, message: str = None, data: str = None):
    return {"status": status, "message": message, "data": data}

def reset_serial_numbers(db: Session):
    employees = db.query(Employee).order_by(Employee.id).all()
    for idx, emp in enumerate(employees, start=1):
        emp.sr_no = idx
    db.commit()

# Create employee (protected)
@app.post("/employees/")
def create_employee(emp: EmployeeSchema, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_emp = Employee(
        sr_no=0,
        name=emp.name,
        salary=emp.salary,
        department=emp.department,
        joindate=emp.joindate,
        profile_pic=emp.profile_pic
    )
    db.add(new_emp)
    db.commit()
    reset_serial_numbers(db)
    db.refresh(new_emp)
    return response_message("success", "New row is added", new_emp.__dict__)

# Read all (protected)
@app.get("/employees/")
def get_employees(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employees = db.query(Employee).order_by(Employee.sr_no).all()
    if not employees:
        return response_message("failed", "No data in table")
    return response_message("success", data=[emp.__dict__ for emp in employees])