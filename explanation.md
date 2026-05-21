# SyncFlow Project Documentation & Workflow Architecture

SyncFlow is a premium team task scheduling suite designed with a sleek dark glassmorphism theme, robust Flask cookie-based session security, and customized Role-Based Access Control (RBAC).

---

## 1. Project Workflow

The application operates with three distinct user roles:
1. **Master Admin (`role='Master'`)**:
   - The system's superuser (default account: `Ethara.Ai` / `admin@gmail.com` / `admin123`).
   - Has global visibility across **all** projects, tasks, managers, and employees.
   - Monitors overall team activity, metrics, and progress.
2. **Manager (`role='Admin'`)**:
   - Manages team environments (formerly "Admin" in visual terminology).
   - Restricted to viewing and managing **only projects they created**.
   - Can create projects, add/remove employees from projects, and create or assign tasks.
3. **Employee (`role='Member'`)**:
   - The execution layer of the organization (formerly "Member").
   - Restricted to viewing and updating **only tasks explicitly assigned to them**.
   - Updates task statuses (Todo $\rightarrow$ In Progress $\rightarrow$ Done) which dynamically updates project metrics.

### Authentication & Redirection Flow
- Users start on the welcome landing page (`/`). They can click any profile in the **Premium Seed Profiles** grid to auto-fill credentials.
- After logging in:
  - Users with role `Admin` or `Master` are redirected to `/admin-dashboard` (Manager view).
  - Users with role `Member` are redirected to `/member-dashboard` (Employee view).
- If a user attempts to access a dashboard route manually without proper auth/role permission, the backend redirects them to `/login` or the correct dashboard corresponding to their active session role.

---

## 2. Database Schema Design (SQLite)

The database schema is defined in [models.py](file:///c:/Users/HP/Downloads/Assinment'/models.py) using Flask-SQLAlchemy. It consists of four main tables:

### A. Users Table (`users`)
Stores user accounts and authentication credentials.
- `id` (Integer, Primary Key)
- `name` (String, Not Null): Full name of the user.
- `email` (String, Unique, Not Null): Login email address.
- `password_hash` (String, Not Null): Securely hashed password.
- `role` (String, Default 'Member'): Restructured access control roles:
  - `'Master'`: System Master Admin
  - `'Admin'`: Manager
  - `'Member'`: Employee
- `created_at` (DateTime, Default UTC Now)

### B. Projects Table (`projects`)
Represents projects created by managers.
- `id` (Integer, Primary Key)
- `name` (String, Not Null): Project name.
- `description` (Text): Details of the project.
- `created_by_id` (Integer, Foreign Key $\rightarrow$ `users.id`): Tracks which manager created the project.
- `created_at` (DateTime, Default UTC Now)

### C. Project Members Table (`project_members`)
A join-table defining many-to-many relationships between projects and users.
- `id` (Integer, Primary Key)
- `project_id` (Integer, Foreign Key $\rightarrow$ `projects.id`, Cascade On Delete)
- `user_id` (Integer, Foreign Key $\rightarrow$ `users.id`, Cascade On Delete)
- `joined_at` (DateTime, Default UTC Now)

### D. Tasks Table (`tasks`)
Defines the items of work inside projects.
- `id` (Integer, Primary Key)
- `title` (String, Not Null): Name of the deliverable.
- `description` (Text): Detailed task instruction.
- `status` (String, Default 'Todo'): Options: `'Todo'`, `'In Progress'`, `'Done'`.
- `priority` (String, Default 'Medium'): Options: `'Low'`, `'Medium'`, `'High'`.
- `due_date` (Date): Deadlines.
- `assigned_to_id` (Integer, Foreign Key $\rightarrow$ `users.id`): The employee assigned to this task.
- `project_id` (Integer, Foreign Key $\rightarrow$ `projects.id`, Cascade On Delete): The parent project.
- `created_at` (DateTime, Default UTC Now)

---

## 3. REST API Documentation

The server endpoints in [app.py](file:///c:/Users/HP/Downloads/Assinment'/app.py) provide robust JSON interfaces for CRUD actions and dashboard statistics.

### Auth Endpoints
- **POST `/api/auth/signup`**: Creates a new user profile.
- **POST `/api/auth/login`**: Authenticates a user and sets secure cookies.
- **POST `/api/auth/logout`**: Clears user session cookies.
- **GET `/api/auth/me`**: Returns the current authenticated user context.

### User Directory
- **GET `/api/users`**: Returns all registered users (Enterprise Directory).
- **POST `/api/users`**: *Manager/Master only.* Directly creates user profiles.

### Project Management
- **GET `/api/projects`**: Fetches projects.
  - Master Admin gets all projects.
  - Manager gets only projects they created.
  - Employee gets only projects where they are added as a project member.
- **POST `/api/projects`**: *Manager/Master only.* Creates a project.
- **PUT `/api/projects/<id>`**: *Manager/Master only.* Updates project metadata.
- **DELETE `/api/projects/<id>`**: *Manager/Master only.* Deletes project and cascades delete tasks.

### Project Membership Management
- **GET `/api/projects/<project_id>/members`**: Retrieves members assigned to the project.
- **POST `/api/projects/<project_id>/members`**: *Manager/Master only.* Adds a member.
- **DELETE `/api/projects/<project_id>/members/<user_id>`**: *Manager/Master only.* Removes a member.

### Task Management
- **GET `/api/tasks`**:
  - Master Admin gets all tasks.
  - Manager gets all tasks in projects they created.
  - Employee gets all tasks assigned to them.
- **GET `/api/projects/<project_id>/tasks`**: Fetches tasks inside a project.
  - Master/Manager gets all tasks in the project.
  - Employee gets only their assigned tasks in the project.
- **POST `/api/projects/<project_id>/tasks`**: *Manager/Master only.* Creates a new task.
- **PUT `/api/tasks/<task_id>`**:
  - Manager/Master can edit all fields (title, description, priority, assignee, status).
  - Employee can only update the `status` field.
- **DELETE `/api/tasks/<task_id>`**: *Manager/Master only.* Deletes a task.

### Analytics Dashboard
- **GET `/api/dashboard/stats`**: Computes statistics:
  - Scoped dynamically based on the current user's role.
  - Returns `total_tasks`, status counts (`todo_tasks`, `progress_tasks`, `done_tasks`), `overdue_count`, lists of `overdue_tasks`, lists of `recent_tasks`, and a `project_progress` list detailing completion percentage per project.
