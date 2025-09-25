# from fastapi import FastAPI
# from pydantic import BaseModel
# import json
# from typing import Optional

# app = FastAPI()

# with open("data.json") as f:
#     employees = json.load(f)

# class Employees(BaseModel):
#     id : int
#     username : str
#     salary : int
#     dept : str
#     joindate : str

# class New_Employees(BaseModel):
#     id : Optional[int] = None
#     username : Optional[str] = None
#     salary : Optional[int] = None
#     dept : Optional[str] = None
#     joindate : Optional[str] = None

# # to get all employees detalies 
# @app.get("/employees")
# def get_employee():
#     return employees

# # to get employee by id
# @app.get("/employees/{id}")
# def get_id(id:int):
#     for emp in employees:
#         if emp["id"] == id:
#             return emp

# # to add new employee 
# @app.post("/employees")
# def add_employee(emp: Employees):
#     employees.append(emp.dict())
#     return {"message": "Employee added successfully", "employee": emp}

# # to update the existing employee
# @app.put("/employees/{id}")
# def update_employee(id: int, emp: Employees):
#     for i, e in enumerate(employees):
#         if e["id"] == id:
#             employees[i] = emp.dict()
#             return {"message": "Employee updated", "employee": emp}

# #to delete an employee 
# @app.delete("/employees/{id}")
# def delete_employee(id:int):
#     for i , e in enumerate(employees):
#         if e["id"] == id:
#             removed = employees.pop(i)
#             return {"message": "employee removed","employee":removed}

# #to update any particular data in employee
# @app.patch("/employees/{id}")
# def patch_employee(id:int , emp:New_Employees):
#     for i in employees:
#         if i["id"] == id:
#             new_value = emp.dict(exclude_unset=True)
#             i.update(new_value)
#             return(i)













from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import Employee
from database import engine, Base , get_db
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

Base.metadata.create_all(bind=engine)

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
    return {
        "status": status,
        "message": message,
        "data": data
    }

def reset_serial_numbers(db: Session):
    employees = db.query(Employee).order_by(Employee.id).all()
    for idx, emp in enumerate(employees, start=1):
        emp.sr_no = idx
    db.commit()


# create
@app.post("/employees/")
def create_employee(emp: EmployeeSchema, db: Session = Depends(get_db)):
    employees = db.query(Employee).filter(Employee.name == emp.name,
    Employee.department == emp.department).first()
    if employees:
        return response_message("failed", "data existing in table",employees)
    else:
        new_emp = Employee(
            sr_no=0,
            name=emp.name,
            salary=emp.salary,
            department=emp.department,
            joindate=emp.joindate,
            profile_pic = emp.profile_pic
        )
    db.add(new_emp)
    db.commit()
    reset_serial_numbers(db)
    db.refresh(new_emp)
    return response_message("success", "New row is added", new_emp.__dict__)

# read all
@app.get("/employees/")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.sr_no).all()
    if not employees:
        return response_message("failed", "No data in table")
    return response_message("success", data=[emp.__dict__ for emp in employees])

# read by id
@app.get("/employees/{emp_id}")
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        return response_message("failed", "Employee not found")
    return response_message("success", data=employee.__dict__)

# update
@app.put("/employees/{emp_id}")
def update_employee(emp_id: int, emp: EmployeeSchema, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        return response_message("failed", "Employee not found")

    employee.name = emp.name
    employee.salary = emp.salary
    employee.department = emp.department
    employee.joindate = emp.joindate
    employee.profile_pic = emp.profile_pic
    db.commit()
    reset_serial_numbers(db)
    db.refresh(employee)
    return response_message("success", "Employee updated", employee.__dict__)

# patch
@app.patch("/employees/{emp_id}")
def update_employee(emp_id: int, emp: EmployeeUpdateSchema, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        return response_message("failed", "Employee not found")

    # Update only given
    if emp.name is not None:
        employee.name = emp.name
    if emp.salary is not None:
        employee.salary = emp.salary
    if emp.department is not None:
        employee.department = emp.department
    if emp.joindate is not None:
        employee.joindate = emp.joindate
    if emp.profile_pic is not None:
        employee.profile_pic = emp.profile_pic

    db.commit()
    reset_serial_numbers(db)
    db.refresh(employee)
    return response_message("success", "Employee partially updated", employee.__dict__)

# delete
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        return response_message("failed", "Employee not found")
    
    deleted_emp = employee
    db.delete(employee)
    db.commit()
    reset_serial_numbers(db)
    return response_message("success", "Employee deleted",deleted_emp)


