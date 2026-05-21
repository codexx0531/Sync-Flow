from flask import Flask, request, jsonify, session, send_from_directory, redirect
from flask_cors import CORS
from models import db, User, Project, ProjectMember, Task
from datetime import datetime, date, timedelta
import os
from functools import wraps

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'super_secret_anti_gravity_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, supports_credentials=True)
db.init_app(app)

# Helper Decorators for Auth & Role-Based Access Control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized. Please login.'}), 401
        
        # Verify user still exists in database
        current_user = db.session.get(User, session['user_id'])
        if not current_user:
            session.pop('user_id', None)
            return jsonify({'error': 'User not found. Session cleared.'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(current_user, *args, **kwargs):
        if current_user.role != 'Admin':
            return jsonify({'error': 'Forbidden. Admin privileges required.'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function

# Seed Data on Startup (Indian Roster, Projects, and Tasks)
with app.app_context():
    db.create_all()
    
    # Check if database is empty and seed
    if not User.query.filter_by(email='aarav@taskmanager.com').first():
        # 1. Admins
        aarav = User(name='Aarav Sharma', email='aarav@taskmanager.com', role='Admin')
        aarav.set_password('admin123')
        db.session.add(aarav)
        
        ananya = User(name='Ananya Iyer', email='ananya@taskmanager.com', role='Admin')
        ananya.set_password('admin123')
        db.session.add(ananya)
        
        # 2. Members
        vihaan = User(name='Vihaan Patel', email='vihaan@taskmanager.com', role='Member')
        vihaan.set_password('member123')
        db.session.add(vihaan)
        
        diya = User(name='Diya Sen', email='diya@taskmanager.com', role='Member')
        diya.set_password('member123')
        db.session.add(diya)
        
        arjun = User(name='Arjun Verma', email='arjun@taskmanager.com', role='Member')
        arjun.set_password('member123')
        db.session.add(arjun)
        
        sai = User(name='Sai Prasad', email='sai@taskmanager.com', role='Member')
        sai.set_password('member123')
        db.session.add(sai)
        
        # Flush to generate IDs
        db.session.flush()
        
        # 3. Create Seed Projects
        p1 = Project(
            name='Smart City Traffic Controller',
            description='AI-powered traffic signal optimization dashboard for Bengaluru metropolitan area.',
            created_by_id=aarav.id
        )
        db.session.add(p1)
        
        p2 = Project(
            name='UPI Lite Wallet Core',
            description='High-performance offline micro-payments ledger and SDK architecture for Indian banking switches.',
            created_by_id=ananya.id
        )
        db.session.add(p2)
        
        db.session.flush()
        
        # 4. Associate Project Members
        # Project 1 Members (Aarav, Vihaan, Diya)
        db.session.add(ProjectMember(project_id=p1.id, user_id=aarav.id))
        db.session.add(ProjectMember(project_id=p1.id, user_id=vihaan.id))
        db.session.add(ProjectMember(project_id=p1.id, user_id=diya.id))
        
        # Project 2 Members (Ananya, Arjun, Sai)
        db.session.add(ProjectMember(project_id=p2.id, user_id=ananya.id))
        db.session.add(ProjectMember(project_id=p2.id, user_id=arjun.id))
        db.session.add(ProjectMember(project_id=p2.id, user_id=sai.id))
        
        # 5. Populate Seed Tasks with varying statuses and due dates
        today = date.today()
        
        # Project 1 Tasks
        t1 = Task(
            title='Integrate camera feeds with YOLOv8 model',
            description='Set up RTSP video streaming pipeline and optimize traffic camera inputs for vehicle count detection.',
            status='In Progress',
            priority='High',
            due_date=today + timedelta(days=2),
            assigned_to_id=vihaan.id,
            project_id=p1.id
        )
        db.session.add(t1)
        
        t2 = Task(
            title='Design responsive control room dashboard',
            description='Build glassmorphic web dashboard showing active congestion alerts, signal status, and override controls.',
            status='Done',
            priority='Medium',
            due_date=today - timedelta(days=2),
            assigned_to_id=diya.id,
            project_id=p1.id
        )
        db.session.add(t2)
        
        t3 = Task(
            title='Calibrate latency thresholds for SOS alerts',
            description='Ensure fire brigade and ambulance preemption signal overrides trigger and resolve within 400 milliseconds.',
            status='Todo',
            priority='High',
            due_date=today - timedelta(days=3), # Overdue task!
            assigned_to_id=vihaan.id,
            project_id=p1.id
        )
        db.session.add(t3)
        
        # Project 2 Tasks
        t4 = Task(
            title='Draft API cryptographic specifications',
            description='Define AES-GCM and ECDSA message signatures to secure offline ledger transaction sync.',
            status='Done',
            priority='High',
            due_date=today - timedelta(days=1),
            assigned_to_id=arjun.id,
            project_id=p2.id
        )
        db.session.add(t4)
        
        t5 = Task(
            title='Optimize database transactions for SQLite',
            description='Establish thread-locking boundaries to support concurrent writes on lightweight edge wallet devices.',
            status='Todo',
            priority='Medium',
            due_date=today + timedelta(days=4),
            assigned_to_id=sai.id,
            project_id=p2.id
        )
        db.session.add(t5)
        
        db.session.commit()
        print("Database fully populated with Indian names, projects, and active tasks.")

# --- STATIC PAGE ROUTING WITH ROLE REDIRECTS ---

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])
        if current_user:
            if current_user.role == 'Admin':
                return redirect('/admin-dashboard')
            else:
                return redirect('/member-dashboard')
    return app.send_static_file('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])
        if current_user:
            if current_user.role == 'Admin':
                return redirect('/admin-dashboard')
            else:
                return redirect('/member-dashboard')
    return app.send_static_file('register.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    current_user = db.session.get(User, session['user_id'])
    if not current_user or current_user.role != 'Admin':
        # If user is a Member, redirect them to the correct dashboard
        if current_user and current_user.role == 'Member':
            return redirect('/member-dashboard')
        session.pop('user_id', None)
        return redirect('/login')
    return app.send_static_file('admin_dashboard.html')

@app.route('/member-dashboard')
def member_dashboard_():
    if 'user_id' not in session:
        return redirect('/login')
    current_user = db.session.get(User, session['user_id'])
    if not current_user or current_user.role != 'Member':
        # If user is an Admin, redirect them to the correct dashboard
        if current_user and current_user.role == 'Admin':
            return redirect('/admin-dashboard')
        session.pop('user_id', None)
        return redirect('/login')
    return app.send_static_file('member_dashboard.html')

# --- AUTHENTICATION APIS ---

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'Member').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400
    
    if role not in ['Admin', 'Member']:
        return jsonify({'error': 'Invalid role. Must be Admin or Member.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered.'}), 400

    try:
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return jsonify({
            'message': 'Signup successful',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create account: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    session['user_id'] = user.id
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully.'}), 200

@app.route('/api/auth/me', methods=['GET'])
@login_required
def me(current_user):
    return jsonify({
        'user': current_user.to_dict()
    }), 200

# --- USER DIRECTORY APIS ---

@app.route('/api/users', methods=['GET'])
@login_required
def get_users(current_user):
    users = User.query.order_by(User.name).all()
    return jsonify([u.to_dict() for u in users]), 200

@app.route('/api/users', methods=['POST'])
@admin_required
def admin_create_user(current_user):
    """Admin-only endpoint to create user accounts directly without altering active session."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'Member').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400
    
    if role not in ['Admin', 'Member']:
        return jsonify({'error': 'Invalid role. Must be Admin or Member.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered.'}), 400

    try:
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create team member: {str(e)}'}), 500

# --- PROJECT APIS ---

@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects(current_user):
    if current_user.role == 'Admin':
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
        project_ids = [m.project_id for m in memberships]
        projects = Project.query.filter(Project.id.in_(project_ids)).order_by(Project.created_at.desc()).all()
        
    return jsonify([p.to_dict() for p in projects]), 200

@app.route('/api/projects', methods=['POST'])
@admin_required
def create_project(current_user):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Project name is required.'}), 400

    try:
        project = Project(name=name, description=description, created_by_id=current_user.id)
        db.session.add(project)
        db.session.flush()
        
        member = ProjectMember(project_id=project.id, user_id=current_user.id)
        db.session.add(member)
        db.session.commit()
        
        return jsonify(project.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create project: {str(e)}'}), 500

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@admin_required
def update_project(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': 'Project name is required.'}), 400
        
    try:
        project.name = name
        project.description = description
        db.session.commit()
        return jsonify(project.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update project: {str(e)}'}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@admin_required
def delete_project(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete project: {str(e)}'}), 500

# --- PROJECT MEMBERSHIP APIS ---

@app.route('/api/projects/<int:project_id>/members', methods=['GET'])
@login_required
def get_project_members(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
    
    is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()
    if current_user.role != 'Admin' and not is_member:
        return jsonify({'error': 'Access denied. You are not a member of this project.'}), 403

    members = ProjectMember.query.filter_by(project_id=project_id).all()
    return jsonify([m.to_dict() for m in members]), 200

@app.route('/api/projects/<int:project_id>/members', methods=['POST'])
@admin_required
def add_project_member(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    data = request.get_json() or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required.'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    existing = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if existing:
        return jsonify({'error': 'User is already a member of this project.'}), 400

    try:
        member = ProjectMember(project_id=project_id, user_id=user_id)
        db.session.add(member)
        db.session.commit()
        return jsonify(member.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add member: {str(e)}'}), 500

@app.route('/api/projects/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@admin_required
def remove_project_member(current_user, project_id, user_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Membership not found.'}), 404
        
    # Prevent creator from being deleted accidentally
    if project.created_by_id == user_id:
        return jsonify({'error': 'Cannot remove the project creator/admin member.'}), 400
        
    try:
        # If user has active tasks in this project, set task assignee back to NULL
        Task.query.filter_by(project_id=project_id, assigned_to_id=user_id).update({Task.assigned_to_id: None})
        
        db.session.delete(membership)
        db.session.commit()
        return jsonify({'message': 'Member removed from project successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to remove member: {str(e)}'}), 500

# --- TASK APIS ---

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_all_tasks(current_user):
    if current_user.role == 'Admin':
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
        project_ids = [m.project_id for m in memberships]
        tasks = Task.query.filter(Task.project_id.in_(project_ids)).order_by(Task.created_at.desc()).all()
        
    return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def get_project_tasks(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
    
    is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()
    if current_user.role != 'Admin' and not is_member:
        return jsonify({'error': 'Access denied. You are not a member of this project.'}), 403

    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@admin_required
def create_task(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'Medium').strip()
    due_date_str = data.get('due_date')
    assigned_to_id = data.get('assigned_to_id')

    if not title:
        return jsonify({'error': 'Task title is required.'}), 400

    if priority not in ['Low', 'Medium', 'High']:
        return jsonify({'error': 'Invalid priority level.'}), 400

    parsed_due_date = None
    if due_date_str:
        try:
            parsed_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if parsed_due_date < date.today():
                return jsonify({'error': 'Due date cannot be in the past.'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid due date format. Use YYYY-MM-DD.'}), 400

    if assigned_to_id:
        is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=assigned_to_id).first()
        if not is_member:
            return jsonify({'error': 'Assigned user must be a member of this project.'}), 400

    try:
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=parsed_due_date,
            assigned_to_id=assigned_to_id,
            project_id=project_id,
            status='Todo'
        )
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create task: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(current_user, task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task not found.'}), 404
    
    project_member = ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user.id).first()
    if current_user.role != 'Admin' and not project_member:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json() or {}
    
    if current_user.role == 'Admin':
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', '').strip()
        due_date_str = data.get('due_date')
        assigned_to_id = data.get('assigned_to_id')
        status = data.get('status', '').strip()

        if title:
            task.title = title
        if description is not None:
            task.description = description
        if status:
            if status not in ['Todo', 'In Progress', 'Done']:
                return jsonify({'error': 'Invalid status.'}), 400
            task.status = status
        if priority:
            if priority not in ['Low', 'Medium', 'High']:
                return jsonify({'error': 'Invalid priority.'}), 400
            task.priority = priority
            
        if due_date_str is not None:
            if due_date_str == '':
                task.due_date = None
            else:
                try:
                    task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid due date format. Use YYYY-MM-DD.'}), 400

        if assigned_to_id is not None:
            if assigned_to_id == '':
                task.assigned_to_id = None
            else:
                is_member = ProjectMember.query.filter_by(project_id=task.project_id, user_id=assigned_to_id).first()
                if not is_member:
                    return jsonify({'error': 'Assigned user must be a member of this project.'}), 400
                task.assigned_to_id = assigned_to_id
    else:
        status = data.get('status', '').strip()
        if not status:
            return jsonify({'error': 'Status is required for update.'}), 400
        if status not in ['Todo', 'In Progress', 'Done']:
            return jsonify({'error': 'Invalid status.'}), 400
        task.status = status

    try:
        db.session.commit()
        return jsonify(task.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update task: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@admin_required
def delete_task(current_user, task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task not found.'}), 404
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete task: {str(e)}'}), 500

# --- DASHBOARD / STATS API ---

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats(current_user):
    today = date.today()

    if current_user.role == 'Admin':
        total_tasks = Task.query.count()
        todo_tasks = Task.query.filter_by(status='Todo').count()
        progress_tasks = Task.query.filter_by(status='In Progress').count()
        done_tasks = Task.query.filter_by(status='Done').count()
        
        overdue_tasks = Task.query.filter(
            Task.due_date < today,
            Task.status != 'Done'
        ).all()
        
        projects = Project.query.all()
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    else:
        memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
        project_ids = [m.project_id for m in memberships]
        
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        
        all_project_tasks_query = Task.query.filter(Task.project_id.in_(project_ids))
        total_tasks = all_project_tasks_query.count()
        todo_tasks = all_project_tasks_query.filter_by(status='Todo').count()
        progress_tasks = all_project_tasks_query.filter_by(status='In Progress').count()
        done_tasks = all_project_tasks_query.filter_by(status='Done').count()
        
        overdue_tasks = all_project_tasks_query.filter(
            Task.due_date < today,
            Task.status != 'Done'
        ).all()
        
        recent_tasks = all_project_tasks_query.order_by(Task.created_at.desc()).limit(5).all()

    project_progress = []
    for p in projects:
        tasks_p = Task.query.filter_by(project_id=p.id).all()
        total_p = len(tasks_p)
        done_p = sum(1 for t in tasks_p if t.status == 'Done')
        progress = int((done_p / total_p * 100)) if total_p > 0 else 0
        
        project_progress.append({
            'id': p.id,
            'name': p.name,
            'total_tasks': total_p,
            'done_tasks': done_p,
            'progress': progress
        })

    return jsonify({
        'total_tasks': total_tasks,
        'todo_tasks': todo_tasks,
        'progress_tasks': progress_tasks,
        'done_tasks': done_tasks,
        'overdue_count': len(overdue_tasks),
        'overdue_tasks': [t.to_dict() for t in overdue_tasks],
        'project_progress': project_progress,
        'recent_tasks': [t.to_dict() for t in recent_tasks]
    }), 200

if __name__ == '__main__':
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open('http://127.0.0.1:5000/')

    # Only open browser on the main reloader thread to prevent opening twice in debug mode
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        Timer(1.0, open_browser).start()

    app.run(debug=True, host='127.0.0.1', port=5000)
