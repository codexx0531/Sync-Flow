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
        if current_user.role != 'Admin' and current_user.role != 'Master':
            return jsonify({'error': 'Forbidden. Admin or Master privileges required.'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function

# Seed Data on Startup (Indian Roster, Projects, and Tasks)
with app.app_context():
    db.create_all()
    
    # Check if database is empty and seed
    if not User.query.filter_by(email='admin@gmail.com').first():
        # 0. Master Admin
        master = User(name='Ethara.Ai', email='admin@gmail.com', role='Master')
        master.set_password('admin123')
        db.session.add(master)

        # 1. Admins (Managers)
        aarav = User(name='Aarav Sharma', email='aarav@taskmanager.com', role='Admin')
        aarav.set_password('admin123')
        db.session.add(aarav)
        
        ananya = User(name='Ananya Iyer', email='ananya@taskmanager.com', role='Admin')
        ananya.set_password('admin123')
        db.session.add(ananya)

        rohan = User(name='Rohan Gupta', email='rohan@taskmanager.com', role='Admin')
        rohan.set_password('admin123')
        db.session.add(rohan)

        aditi = User(name='Aditi Rao', email='aditi@taskmanager.com', role='Admin')
        aditi.set_password('admin123')
        db.session.add(aditi)
        
        # 2. Members (Employees)
        employees_data = [
            ('Vihaan Patel', 'vihaan@taskmanager.com'),
            ('Diya Sen', 'diya@taskmanager.com'),
            ('Arjun Verma', 'arjun@taskmanager.com'),
            ('Sai Prasad', 'sai@taskmanager.com'),
            ('Neha Reddy', 'neha@taskmanager.com'),
            ('Kabir Mehta', 'kabir@taskmanager.com'),
            ('Priya Nair', 'priya@taskmanager.com'),
            ('Rahul Joshi', 'rahul@taskmanager.com'),
            ('Siddharth Rao', 'siddharth@taskmanager.com'),
            ('Ishaan Roy', 'ishaan@taskmanager.com'),
            ('Kavya Pillai', 'kavya@taskmanager.com'),
            ('Devendra Singh', 'devendra@taskmanager.com'),
            ('Meera Deshmukh', 'meera@taskmanager.com'),
            ('Pranav Shah', 'pranav@taskmanager.com'),
            ('Anjali Bose', 'anjali@taskmanager.com')
        ]
        
        employees = []
        for name, email in employees_data:
            emp = User(name=name, email=email, role='Member')
            emp.set_password('member123')
            db.session.add(emp)
            employees.append(emp)
            
        # Flush to generate IDs
        db.session.flush()
        
        # 3. Create Seed Projects (8-9 projects)
        projects_data = [
            ('Smart City Traffic Controller', 'AI-powered traffic signal optimization dashboard for Bengaluru metropolitan area.', aarav),
            ('UPI Lite Wallet Core', 'High-performance offline micro-payments ledger and SDK architecture for Indian banking switches.', ananya),
            ('E-Agriculture Advisory Platform', 'Digital portal providing soil health monitoring and crop advisories to farmers.', rohan),
            ('Aadhaar Verification Gateway', 'Highly secure KYC and biometric validation middleware gateway.', aditi),
            ('Railway Freight Optimizer', 'AI logistics module to optimize rake allocations and route planning for Indian Railways.', aarav),
            ('Rural Solar Microgrid Monitor', 'IoT monitoring console measuring power generation and distribution dynamics across villages.', ananya),
            ('Ayushman Bharat Health Registry', 'Standardized medical data indexing system supporting digital health locker integrations.', rohan),
            ('ONDC Adaptor Suite', 'Standardized open protocol schema translation layers for quick buyer-seller app onboarding.', aditi),
            ('Clean Ganga Monitoring Sensors', 'Environmental sensor dashboard checking pH, dissolved oxygen, and turbidities.', rohan)
        ]
        
        projects = []
        for name, desc, manager in projects_data:
            p = Project(name=name, description=desc, created_by_id=manager.id)
            db.session.add(p)
            projects.append(p)
            
        db.session.flush()

        # Add project managers to their projects
        for p in projects:
            db.session.add(ProjectMember(project_id=p.id, user_id=p.created_by_id))
            
        # Map employees to projects
        proj_emp_map = {
            0: [0, 1, 5],
            1: [2, 3, 4],
            2: [6, 7, 8],
            3: [9, 10, 11],
            4: [12, 13, 14],
            5: [0, 1],
            6: [2, 3, 4],
            7: [5, 6, 7],
            8: [8, 9]
        }
        
        for p_idx, emp_indices in proj_emp_map.items():
            for e_idx in emp_indices:
                db.session.add(ProjectMember(project_id=projects[p_idx].id, user_id=employees[e_idx].id))
                
        db.session.flush()
        
        # 5. Populate Seed Tasks with varying statuses and due dates (20 to 30 tasks)
        today = date.today()
        
        tasks_data = [
            ('Optimize YOLOv8 traffic camera integration', 'Set up RTSP video streaming pipeline and optimize traffic camera inputs for vehicle count detection.', 'In Progress', 'High', today + timedelta(days=2), employees[0], projects[0]),
            ('Design real-time traffic signal override panel', 'Build glassmorphic web dashboard showing active congestion alerts, signal status, and override controls.', 'Done', 'Medium', today - timedelta(days=2), employees[1], projects[0]),
            ('Verify preemption latency metrics', 'Ensure fire brigade and ambulance preemption signal overrides trigger and resolve within 400 milliseconds.', 'Todo', 'High', today - timedelta(days=3), employees[5], projects[0]),
            
            ('Implement ECDSA transaction signing', 'Define secure offline cryptographic routines on mobile SDK layers.', 'Done', 'High', today - timedelta(days=1), employees[2], projects[1]),
            ('Resolve database concurrency on SQLite', 'Establish thread-locking boundaries to support concurrent edge ledger writes.', 'Todo', 'Medium', today + timedelta(days=4), employees[3], projects[1]),
            ('Benchmark edge ledger synchronization', 'Perform telemetry check on network sync payloads across unstable rural towers.', 'In Progress', 'High', today + timedelta(days=1), employees[4], projects[1]),
            
            ('Deploy regional soil health model', 'Publish multi-spectral imagery classification endpoints to parse Nitrogen-Phosphorus ratios.', 'Todo', 'Low', today + timedelta(days=5), employees[6], projects[2]),
            ('Design bilingual SMS alert gateway', 'Localize agricultural advisory push dispatch triggers in Hindi and Kannada.', 'Done', 'Medium', today - timedelta(days=5), employees[7], projects[2]),
            ('Integrate IMD weather forecasts API', 'Consume automated Indian Meteorological Department seasonal rain warnings.', 'In Progress', 'High', today + timedelta(days=3), employees[8], projects[2]),
            
            ('Review UIDAI biometric compliance specs', 'Validate auth packets header format against official UIDAI technical guidelines.', 'Done', 'High', today - timedelta(days=4), employees[9], projects[3]),
            ('Optimize request processing queue', 'Configure Celery/Redis worker patterns to smooth out transaction bursts.', 'Todo', 'Medium', today - timedelta(days=1), employees[10], projects[3]),
            ('Implement rate limiting policy on gateway', 'Enforce token bucket restrictions per API consumer application.', 'In Progress', 'Medium', today + timedelta(days=6), employees[11], projects[3]),
            
            ('Draft route optimization algorithms', 'Establish genetic algorithm fitness metrics to map coal rake assignments.', 'Todo', 'High', today + timedelta(days=8), employees[12], projects[4]),
            ('Design live wagon tracking map widget', 'Map real-time coordinates feeds onto leaflet-based web visualizer canvas.', 'In Progress', 'Medium', today + timedelta(days=2), employees[13], projects[4]),
            ('Integrate GPS sensors webhook receiver', 'Parse HTTP posts emitted from active rolling stock transmitter modules.', 'Done', 'Medium', today - timedelta(days=6), employees[14], projects[4]),
            
            ('Optimize telemetry packet sizes', 'Compress battery status JSON strings to binary protocol buffers format.', 'Done', 'Low', today - timedelta(days=2), employees[0], projects[5]),
            ('Configure automatic battery low alert threshold', 'Trigger notification events when charge levels drop below 15 percent.', 'In Progress', 'High', today + timedelta(days=4), employees[1], projects[5]),
            
            ('Enforce HIPAA & ABDM privacy consent gates', 'Implement secure JWT-based access controls for third-party record requests.', 'In Progress', 'High', today + timedelta(days=2), employees[2], projects[6]),
            ('Develop user consent logs export', 'Allow patients to export logs in machine-readable JSON format.', 'Todo', 'Low', today + timedelta(days=7), employees[3], projects[6]),
            ('Conduct patient registry query load test', 'Simulate 10,000 concurrent health records lookups using locust.', 'Done', 'Medium', today - timedelta(days=3), employees[4], projects[6]),
            
            ('Implement Beckn protocol search gateway', 'Map internal catalog listings structure into standardized Beckn searches.', 'In Progress', 'High', today + timedelta(days=1), employees[5], projects[7]),
            ('Validate catalog payload transformations', 'Confirm category schema alignments across local seller lists.', 'Todo', 'Medium', today + timedelta(days=5), employees[6], projects[7]),
            ('Design refund settlement workflows', 'Configure webhook endpoints to monitor escrow payments status.', 'Done', 'High', today - timedelta(days=2), employees[7], projects[7]),
            
            ('Establish pH level outlier webhooks', 'Send critical warnings to local municipal authority channels on contamination.', 'Todo', 'Medium', today - timedelta(days=2), employees[8], projects[8]),
            ('Generate weekly water quality report dashboard', 'Draft automated PDF rendering system plotting daily pollutant graphs.', 'In Progress', 'Low', today + timedelta(days=3), employees[9], projects[8])
        ]
        
        for title, desc, status, priority, due, emp, proj in tasks_data:
            t = Task(
                title=title,
                description=desc,
                status=status,
                priority=priority,
                due_date=due,
                assigned_to_id=emp.id,
                project_id=proj.id
            )
            db.session.add(t)
            
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
            if current_user.role == 'Admin' or current_user.role == 'Master':
                return redirect('/admin-dashboard')
            else:
                return redirect('/member-dashboard')
    return app.send_static_file('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])
        if current_user:
            if current_user.role == 'Admin' or current_user.role == 'Master':
                return redirect('/admin-dashboard')
            else:
                return redirect('/member-dashboard')
    return app.send_static_file('register.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    current_user = db.session.get(User, session['user_id'])
    if not current_user or (current_user.role != 'Admin' and current_user.role != 'Master'):
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
        # If user is an Admin or Master, redirect them to the correct dashboard
        if current_user and (current_user.role == 'Admin' or current_user.role == 'Master'):
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
    if current_user.role == 'Master':
        projects = Project.query.order_by(Project.created_at.desc()).all()
    elif current_user.role == 'Admin':
        projects = Project.query.filter_by(created_by_id=current_user.id).order_by(Project.created_at.desc()).all()
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
        
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only update their own projects.'}), 403

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
        
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only delete their own projects.'}), 403

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
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only view members of their own projects.'}), 403
    elif current_user.role == 'Member' and not is_member:
        return jsonify({'error': 'Access denied. You are not a member of this project.'}), 403

    members = ProjectMember.query.filter_by(project_id=project_id).all()
    return jsonify([m.to_dict() for m in members]), 200

@app.route('/api/projects/<int:project_id>/members', methods=['POST'])
@admin_required
def add_project_member(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only add members to their own projects.'}), 403

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
        
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only remove members from their own projects.'}), 403

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
    if current_user.role == 'Master':
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    elif current_user.role == 'Admin':
        projects = Project.query.filter_by(created_by_id=current_user.id).all()
        project_ids = [p.id for p in projects]
        tasks = Task.query.filter(Task.project_id.in_(project_ids)).order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(assigned_to_id=current_user.id).order_by(Task.created_at.desc()).all()
        
    return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def get_project_tasks(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
    
    is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only view tasks of their own projects.'}), 403
    elif current_user.role == 'Member' and not is_member:
        return jsonify({'error': 'Access denied. You are not a member of this project.'}), 403

    if current_user.role == 'Master' or current_user.role == 'Admin':
        tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(project_id=project_id, assigned_to_id=current_user.id).order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@admin_required
def create_task(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
        
    if current_user.role == 'Admin' and project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only create tasks in their own projects.'}), 403

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
            new_member = ProjectMember(project_id=project_id, user_id=assigned_to_id)
            db.session.add(new_member)

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
    if current_user.role == 'Admin' and task.project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only update tasks in their own projects.'}), 403
    elif current_user.role == 'Member' and (not project_member or task.assigned_to_id != current_user.id):
        return jsonify({'error': 'Access denied. You can only update tasks assigned to you.'}), 403

    data = request.get_json() or {}
    
    if current_user.role == 'Admin' or current_user.role == 'Master':
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
                    new_member = ProjectMember(project_id=task.project_id, user_id=assigned_to_id)
                    db.session.add(new_member)
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
        
    if current_user.role == 'Admin' and task.project.created_by_id != current_user.id:
        return jsonify({'error': 'Access denied. Managers can only delete tasks in their own projects.'}), 403
        
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

    if current_user.role == 'Master':
        projects = Project.query.order_by(Project.created_at.desc()).all()
        tasks_query = Task.query
    elif current_user.role == 'Admin':
        projects = Project.query.filter_by(created_by_id=current_user.id).order_by(Project.created_at.desc()).all()
        project_ids = [p.id for p in projects]
        tasks_query = Task.query.filter(Task.project_id.in_(project_ids))
    else:
        memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
        project_ids = [m.project_id for m in memberships]
        projects = Project.query.filter(Project.id.in_(project_ids)).order_by(Project.created_at.desc()).all()
        tasks_query = Task.query.filter_by(assigned_to_id=current_user.id)

    total_tasks = tasks_query.count()
    todo_tasks = tasks_query.filter_by(status='Todo').count()
    progress_tasks = tasks_query.filter_by(status='In Progress').count()
    done_tasks = tasks_query.filter_by(status='Done').count()
    
    overdue_tasks = tasks_query.filter(
        Task.due_date < today,
        Task.status != 'Done'
    ).all()
    
    recent_tasks = tasks_query.order_by(Task.created_at.desc()).limit(5).all()

    project_progress = []
    for p in projects:
        if current_user.role == 'Master' or current_user.role == 'Admin':
            tasks_p = Task.query.filter_by(project_id=p.id).all()
        else:
            tasks_p = Task.query.filter_by(project_id=p.id, assigned_to_id=current_user.id).all()
            
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
    # Detect port from environment variable (required for platforms like Railway)
    port = int(os.environ.get('PORT', 5000))
    
    # Detect production/Railway hosting environment
    is_production = 'PORT' in os.environ
    host = '0.0.0.0' if is_production else '127.0.0.1'
    
    # Enable debug locally, disable in production
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1' if not is_production else False
    
    # Disable Werkzeug watchdog reloader on Windows to prevent OSError: [WinError 10038]
    use_reloader = False if os.name == 'nt' else debug_mode
    
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open(f'http://127.0.0.1:{port}/')

    # Only attempt to open the browser locally (not in headless production/Railway containers)
    if not is_production and debug_mode:
        # If reloader is enabled, wait for the actual worker thread to open the browser once
        if not use_reloader or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            Timer(1.0, open_browser).start()

    print(f" * SyncFlow starting on {host}:{port} (debug={debug_mode}, reloader={use_reloader})")
    app.run(debug=debug_mode, host=host, port=port, use_reloader=use_reloader)

