# FastAPI JWT CRUD Project 🚀

This is a **FastAPI + MySQL** project that demonstrates:
- **JWT Authentication** (login for `admin`, `manager`, and `employee` roles)
- **User Management** (register single or multiple users at once)
- **Employee CRUD Operations** (Create, Read, Update, Delete employees)
- **Pagination, Filtering, Sorting, and Search** on employee records

The project is lightweight and focuses only on the **essential FastAPI + SQLAlchemy + JWT** setup, making it easy to learn and extend.

---

## ⚙️ Features

- 🔑 **JWT-based Authentication**
  - `/register` → Register new user(s) with role (`admin`, `manager`, `employee`)
  - `/token` → Login and get JWT access token
- 👨‍💼 **Role-based Authorization**
  - `admin` → Can create, update, delete employees  
  - `manager` → Can update employees  
  - `employee` → Can only view employees
- 📋 **Employee CRUD**
  - Create employee (admin only)
  - Read employees (all users)
  - Update employee (admin/manager only)
  - Delete employee (admin only)
- 🔍 **Advanced Employee Listing**
  - Pagination (`page`, `size`)
  - Filtering (`department`, `min_salary`, `max_salary`)
  - Search (`name`)
  - Sorting (`id`, `name`, `salary`, `joindate`)
