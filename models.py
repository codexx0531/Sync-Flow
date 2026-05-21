from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='Member', nullable=False) # 'Admin' or 'Member'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_projects = db.relationship('Project', backref='creator', lazy=True, cascade="all, delete-orphan")
    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True)
    project_memberships = db.relationship('ProjectMember', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade="all, delete-orphan")
    project_members = db.relationship('ProjectMember', backref='project', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='_project_user_uc'),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None
        }

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Todo', nullable=False) # 'Todo', 'In Progress', 'Done'
    priority = db.Column(db.String(20), default='Medium', nullable=False) # 'Low', 'Medium', 'High'
    due_date = db.Column(db.Date, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assigned_to_id': self.assigned_to_id,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
