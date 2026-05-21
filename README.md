# SyncFlow | Premium Team Task Manager

SyncFlow is a beautiful, high-fidelity, role-based Team Task Manager built with a secure **Python Flask** backend and a custom **glassmorphic dark-theme** frontend. It leverages a robust role-based access control (RBAC) model to divide functionalities between **Master Admin**, **Managers**, and **Employees** across standalone secure pages.

---

## 🚀 Key Features

*   **Secure Session-Based Routing**: Server-side checks enforce page and API access boundaries. Logged-out users are redirected to `/login`, while authenticated users are directed to `/admin-dashboard` (for Master Admin and Managers) or `/member-dashboard` (for Employees) based on their role.
*   **Three-Tier Dashboard Views**:
    *   **Master Admin Console**: View all projects, managers, employees, and tasks across the entire platform.
    *   **Manager Console**: Create and manage owned projects, assign employees, directly provision new user accounts, create tasks with deadlines and priorities, and delete tasks/projects.
    *   **Employee Console**: View assigned projects, view collaborating teammates, and update the progress status of assigned tasks.
*   **Interactive Kanban Board**: Dynamic status columns (`Todo`, `In Progress`, `Done`) with on-the-fly filters for Project, Priority, and Status.
*   **Workspace Analytics**: Fully integrated `Chart.js` doughnut chart showing task status breakdown, project-wise progress completion trackers, and a critical overdue tasks list.
*   **Realistic Indian Roster**: Automatically pre-seeded with realistic Indian staff members, projects, and active tasks on the first startup.

---

## 🛠️ Codebase Directory Structure

```text
├── app.py                  # Secure Flask server, REST APIs, and database seeder
├── models.py               # SQLAlchemy models (User, Project, ProjectMember, Task)
├── requirements.txt        # Production dependencies (Flask, Flask-SQLAlchemy, Flask-Cors)
└── static/                 # Glassmorphic frontend assets
    ├── login.html          # Authentication portal page
    ├── register.html       # Enterprise sign-up page
    ├── admin_dashboard.html# Administrator console template
    ├── member_dashboard.html# Read-only Member dashboard template
    ├── css/
    │   └── style.css       # Unified glassmorphic visual system styling stylesheet
    └── js/
        ├── login.js        # Authentication payload dispatcher
        ├── register.js     # Signup controller
        ├── admin.js        # Admin interaction controller, stats engine, and forms
        └── member.js       # Member interaction controller & status update dispatcher
```

---

## 💡 Quick Access Test Accounts (Seeded)

The database automatically seeds the Master Admin, 4 Managers, and 15 Employees for effortless evaluation. A complete roster containing all emails, passwords, and name lists is saved in the [credential](file:///c:/Users/HP/Downloads/Assinment'/credential) file in the project root.

Below is a quick reference table of key seeded profiles:

| System Role (Concept) | Database Role (Code) | Employee Name | Email Address | Password |
| :--- | :--- | :--- | :--- | :--- |
| **Master Admin** | `Master` | Ethara.Ai | `admin@gmail.com` | `admin123` |
| **Manager** | `Admin` | Aarav Sharma | `aarav@taskmanager.com` | `admin123` |
| **Manager** | `Admin` | Ananya Iyer | `ananya@taskmanager.com` | `admin123` |
| **Employee** | `Member` | Vihaan Patel | `vihaan@taskmanager.com` | `member123` |
| **Employee** | `Member` | Diya Sen | `diya@taskmanager.com` | `member123` |
| **Employee** | `Member` | Arjun Verma | `arjun@taskmanager.com` | `member123` |

---

## 💻 Installation & Local Run Guide

Follow these steps to run the application locally:

### 1. Prerequisite
Ensure that you have **Python 3.8+** installed on your operating system.

### 2. Install Dependencies
Open your shell/command prompt in the project root directory and execute:
```bash
pip install -r requirements.txt
```

### 3. Start the Server
Launch the Flask development server:
```bash
python app.py
```
Upon launching, Flask will bind to `http://127.0.0.1:5000/` and initialize/seed the SQLite database at `instance/task_manager.db`.

### 4. Open in Browser
Open your browser and navigate to:
```url
http://127.0.0.1:5000/
```
*   Use the **Quick Access Test Accounts** buttons at the bottom of the login card to log in instantly with a single click.

---

## 🔍 Recommended Verification Flow

### 1. Master Admin Verification
1.  Log in as **Ethara.Ai** (`admin@gmail.com` / `admin123`).
2.  Verify that you can see all projects and tasks across all managers in the system.
3.  Monitor the global activities, overall task completion states, and active team sizes.

### 2. Manager Verification
1.  Log in as **Aarav Sharma** (`aarav@taskmanager.com` / `admin123`).
2.  Verify that you only see projects you created (e.g. Smart City Traffic Controller).
3.  Navigate to **Projects** and click **"+ New Project"** to build a new project portfolio.
4.  Click **"Team"** on your project card to assign employees to the workspace.
5.  Navigate to **Team** in the sidebar, and click **"+ Add Employee"** to register a new employee user directly.
6.  Navigate to **Tasks**, click **"+ Create Task"**, fill out details, and assign it to an assigned project employee.
7.  Modify the task's properties inside the Kanban board to verify full manager editing and deletion controls.

### 3. Employee Verification
1.  Log in as **Vihaan Patel** (`vihaan@taskmanager.com` / `member123`).
2.  Verify that you only see projects you are explicitly assigned to.
3.  Navigate to **Tasks** and click on any card. Verify that you can **only update the status dropdown**, while other fields (title, priority, due date) are read-only.
4.  Change the status to `Done` and verify that the Kanban board and Dashboard doughnut chart update dynamically.
