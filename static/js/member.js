/* ==========================================
   SyncFlow Member Dashboard JavaScript Logic
   ========================================== */

// --- Global Application State ---
const State = {
    currentUser: null,
    projects: [],
    tasks: [],
    users: [],
    activeFilters: {
        project: 'all',
        priority: 'all',
        status: 'all'
    },
    charts: {
        status: null
    }
};

// --- API Fetch Client Wrapper ---
const API = {
    async request(url, options = {}) {
        options.credentials = 'include'; // Essential for Flask cookie session persistence
        options.headers = options.headers || {};
        if (options.body && !(options.body instanceof FormData)) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong.');
            }
            return data;
        } catch (error) {
            console.error(`API Error on ${url}:`, error);
            throw error;
        }
    }
};

// --- Initializer on Page Load ---
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Initial State Check
    await checkAuth();

    // 2. Setup Routing and Event Listeners
    window.addEventListener('hashchange', router);
    setupEventListeners();
    
    // 3. Initialize Router
    router();
});

// --- Auth Checker ---
async function checkAuth() {
    try {
        const response = await API.request('/api/auth/me');
        if (!response.user || response.user.role !== 'Member') {
            window.location.href = '/login';
            return;
        }
        State.currentUser = response.user;
        updateUserProfileUI();
    } catch (error) {
        State.currentUser = null;
        window.location.href = '/login';
    }
}

// --- Dynamic Toast Alert System ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'info';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'alert-triangle';

    toast.innerHTML = `
        <i data-lucide="${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    lucide.createIcons();

    // Auto-remove after 3.5 seconds with animation
    setTimeout(() => {
        toast.style.transition = 'all 0.5s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 500);
    }, 3500);
}

// --- Event Listeners Setup ---
function setupEventListeners() {
    // Logout Click
    document.getElementById('logout-button').addEventListener('click', handleLogout);

    // Task Edit Form Submission (Status Update only)
    document.getElementById('task-edit-form').addEventListener('submit', handleTaskEditSubmit);

    // Kanban Filter Selection Events
    document.getElementById('filter-project').addEventListener('change', (e) => {
        State.activeFilters.project = e.target.value;
        renderTasks();
    });
    document.getElementById('filter-priority').addEventListener('change', (e) => {
        State.activeFilters.priority = e.target.value;
        renderTasks();
    });
    document.getElementById('filter-status').addEventListener('change', (e) => {
        State.activeFilters.status = e.target.value;
        renderTasks();
    });
}

// --- Logout Action ---
async function handleLogout() {
    try {
        await API.request('/api/auth/logout', { method: 'POST' });
        State.currentUser = null;
        State.activeFilters = {
            project: 'all',
            priority: 'all',
            status: 'all'
        };
        showToast('Logged out successfully.');
        setTimeout(() => {
            window.location.href = '/login';
        }, 500);
    } catch (err) {
        showToast('Logout failed.', 'error');
    }
}

// --- User Profile Details Loader ---
function updateUserProfileUI() {
    if (!State.currentUser) return;
    
    document.getElementById('profile-name').innerText = State.currentUser.name;
    document.getElementById('profile-role').innerText = State.currentUser.role;
    
    const names = State.currentUser.name.split(' ');
    const initials = names.map(n => n[0]).join('').substring(0, 2).toUpperCase();
    document.getElementById('avatar-initials').innerText = initials;
}

// --- MODALS TOGGLERS ---
window.openModal = function(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
};

window.closeModal = function(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    const form = document.querySelector(`#${modalId} form`);
    if (form) form.reset();
};

// --- SPA Hash Router ---
async function router() {
    if (!State.currentUser) {
        return;
    }

    const hash = window.location.hash || '#dashboard';
    const baseHash = hash.split('?')[0];
    
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    const activeNav = document.getElementById(`nav-${baseHash.substring(1)}`);
    if (activeNav) activeNav.classList.add('active');

    document.querySelectorAll('.content-section').forEach(sec => sec.classList.add('hidden'));
    const targetSection = document.getElementById(`view-${baseHash.substring(1)}`);
    if (targetSection) targetSection.classList.remove('hidden');

    const viewTitle = document.getElementById('view-title');
    const viewSubtitle = document.getElementById('view-subtitle');
    const actionContainer = document.getElementById('header-action-container');
    actionContainer.innerHTML = ''; 

    switch(baseHash) {
        case '#dashboard':
            viewTitle.innerText = 'Workspace Dashboard';
            viewSubtitle.innerText = 'Core analytics and critical task tracking.';
            renderDashboard();
            break;
            
        case '#projects':
            viewTitle.innerText = 'Assigned Projects';
            viewSubtitle.innerText = 'View project portfolios you collaborate on.';
            renderProjects();
            break;
            
        case '#tasks':
            viewTitle.innerText = 'Work Breakdown Schedule';
            viewSubtitle.innerText = 'Kanban status tracker and assignable deliverables.';
            
            const queryStr = hash.split('?')[1];
            if (queryStr) {
                const params = new URLSearchParams(queryStr);
                const projId = params.get('project');
                if (projId) {
                    State.activeFilters.project = projId;
                } else {
                    State.activeFilters.project = 'all';
                }
            } else {
                State.activeFilters.project = 'all';
            }
            
            renderTasksPageSetup();
            break;
            
        case '#members':
            viewTitle.innerText = 'Enterprise Directory';
            viewSubtitle.innerText = 'Directory profile index of collaborating staff.';
            renderMembers();
            break;
            
        default:
            window.location.hash = '#dashboard';
            break;
    }
    
    lucide.createIcons();
}

// ==========================================
// RENDERERS & DATA INTEGRATORS
// ==========================================

// --- 1. RENDER DASHBOARD ---
async function renderDashboard() {
    try {
        const stats = await API.request('/api/dashboard/stats');

        document.getElementById('stat-total-tasks').innerText = stats.total_tasks;
        document.getElementById('stat-pending-tasks').innerText = stats.progress_tasks + stats.todo_tasks;
        document.getElementById('stat-completed-tasks').innerText = stats.done_tasks;
        document.getElementById('stat-overdue-tasks').innerText = stats.overdue_count;

        renderStatusChart(stats.todo_tasks, stats.progress_tasks, stats.done_tasks);
        renderDashboardProjectProgress(stats.project_progress);
        renderDashboardOverdueTasks(stats.overdue_tasks);

    } catch (err) {
        showToast('Failed to load dashboard metrics.', 'error');
    }
}

// Render Doughnut Chart
function renderStatusChart(todo, progress, done) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    
    if (State.charts.status) {
        State.charts.status.destroy();
    }

    if (todo === 0 && progress === 0 && done === 0) {
        State.charts.status = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['No Tasks'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['rgba(255, 255, 255, 0.05)'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
        return;
    }

    State.charts.status = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['To Do', 'In Progress', 'Completed'],
            datasets: [{
                data: [todo, progress, done],
                backgroundColor: [
                    'rgba(99, 102, 241, 0.75)',  
                    'rgba(245, 158, 11, 0.75)',  
                    'rgba(16, 185, 129, 0.75)'   
                ],
                borderColor: ['#111827', '#111827', '#111827'],
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#f3f4f6',
                        font: { family: 'Inter', size: 12 },
                        padding: 15
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// Render Project Progress list on Dashboard
function renderDashboardProjectProgress(projectProgress) {
    const container = document.getElementById('dashboard-project-progress');
    container.innerHTML = '';

    if (!projectProgress || projectProgress.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-lucide="folder"></i>
                <p>No projects assigned to evaluate progress.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    projectProgress.forEach(proj => {
        const item = document.createElement('div');
        item.className = 'project-progress-item';
        item.innerHTML = `
            <div class="project-progress-info">
                <span class="project-progress-name">${proj.name}</span>
                <span class="project-progress-val">${proj.done_tasks}/${proj.total_tasks} Tasks (${proj.progress}%)</span>
            </div>
            <div class="progress-track" title="Click to view tasks" style="cursor: pointer" onclick="window.location.hash = '#tasks?project=${proj.id}'">
                <div class="progress-bar" style="width: ${proj.progress}%"></div>
            </div>
        `;
        container.appendChild(item);
    });
}

// Render Overdue Critical table
function renderDashboardOverdueTasks(overdueTasks) {
    const tbody = document.getElementById('overdue-tasks-table');
    tbody.innerHTML = '';

    if (!overdueTasks || overdueTasks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-secondary">
                    🎉 Excellent! You have no critical overdue tasks.
                </td>
            </tr>
        `;
        return;
    }

    overdueTasks.forEach(task => {
        const tr = document.createElement('tr');
        
        const assigneeName = task.assignee ? task.assignee.name : '<span class="text-secondary">Unassigned</span>';
        let priBadge = `<span class="badge-priority badge-${task.priority.toLowerCase()}">${task.priority}</span>`;
        let statusBadge = `<span class="badge-status badge-${task.status.toLowerCase().replace(' ', '')}">${task.status}</span>`;

        tr.innerHTML = `
            <td><strong>${task.title}</strong></td>
            <td>Project #${task.project_id}</td>
            <td>${assigneeName}</td>
            <td>${priBadge}</td>
            <td class="text-danger"><strong>${task.due_date}</strong></td>
            <td>${statusBadge}</td>
        `;
        
        tr.style.cursor = 'pointer';
        tr.addEventListener('click', () => openTaskDetailsModal(task));
        
        tbody.appendChild(tr);
    });
}

// --- 2. RENDER PROJECTS VIEW ---
async function renderProjects() {
    const container = document.getElementById('projects-container');
    container.innerHTML = '<div class="text-center py-5 text-secondary">Loading your projects...</div>';

    try {
        const projects = await API.request('/api/projects');
        State.projects = projects;
        
        container.innerHTML = '';

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1">
                    <i data-lucide="folder"></i>
                    <h3>No Assigned Projects</h3>
                    <p class="text-secondary mb-3">You are not assigned to any active projects yet. Ask an Administrator to assign you.</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        for (const project of projects) {
            const tasks = await API.request(`/api/projects/${project.id}/tasks`);
            const total = tasks.length;
            const completed = tasks.filter(t => t.status === 'Done').length;
            const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

            const card = document.createElement('div');
            card.className = 'project-card';
            
            card.innerHTML = `
                <div class="project-card-header">
                    <h3>${project.name}</h3>
                    <p class="text-secondary">${project.description || 'No description provided.'}</p>
                </div>
                <div class="project-card-body">
                    <div class="project-progress-info" style="margin-bottom: 0.25rem;">
                        <span class="text-secondary" style="font-size: 0.8rem;">Project Workload</span>
                        <span style="font-size: 0.8rem; font-weight: 500;">${percent}% Complete</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-bar" style="width: ${percent}%"></div>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                        ${completed}/${total} Tasks done
                    </div>
                </div>
                <div class="project-card-actions">
                    <button class="btn btn-secondary btn-sm" onclick="openAddMemberModal(${project.id}, '${project.name.replace(/'/g, "\\'")}')">
                        <i data-lucide="users"></i> Team
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="window.location.hash = '#tasks?project=${project.id}'">
                        <i data-lucide="kanban"></i> View Kanban
                    </button>
                </div>
            `;
            container.appendChild(card);
        }
        lucide.createIcons();
    } catch (err) {
        container.innerHTML = '<div class="text-center py-5 text-danger">Failed to load projects.</div>';
        showToast('Error retrieving project profiles.', 'error');
    }
}

// Read-only member team modal triggers
window.openAddMemberModal = async function(projectId, projectName) {
    // Render current active members
    renderCurrentProjectMembers(projectId);
    window.openModal('modal-member');
};

async function renderCurrentProjectMembers(projectId) {
    const tbody = document.getElementById('current-project-members-tbody');
    tbody.innerHTML = '<tr><td colspan="3" class="text-center">Syncing...</td></tr>';
    
    try {
        const members = await API.request(`/api/projects/${projectId}/members`);
        tbody.innerHTML = '';
        
        if (members.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary">No active team assigned.</td></tr>';
            return;
        }

        members.forEach(m => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td><strong>${m.user.name}</strong></td>
                <td>${m.user.email}</td>
                <td><span class="user-role-badge">${m.user.role}</span></td>
            `;
            tbody.appendChild(tr);
        });
        
        lucide.createIcons();
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Failed to sync membership list.</td></tr>';
    }
}

// --- 3. RENDER TASKS VIEW ---
async function renderTasksPageSetup() {
    const projFilter = document.getElementById('filter-project');
    
    try {
        const projects = await API.request('/api/projects');
        State.projects = projects;
        
        projFilter.innerHTML = '<option value="all">All Assigned Projects</option>';
        projects.forEach(p => {
            projFilter.innerHTML += `<option value="${p.id}">${p.name}</option>`;
        });

        // Ensure dropdown values are in sync with current state
        projFilter.value = State.activeFilters.project;
        document.getElementById('filter-priority').value = State.activeFilters.priority;
        document.getElementById('filter-status').value = State.activeFilters.status;

        renderTasks();

    } catch (err) {
        showToast('Error syncing project folders for filtering.', 'error');
    }
}

async function renderTasks() {
    const todoCards = document.getElementById('cards-todo');
    const progressCards = document.getElementById('cards-progress');
    const doneCards = document.getElementById('cards-done');

    const elements = [todoCards, progressCards, doneCards];
    elements.forEach(el => el.innerHTML = '<div class="text-center py-3 text-secondary" style="font-size:0.8rem">Updating...</div>');

    try {
        let tasks = [];
        
        if (State.activeFilters.project === 'all') {
            tasks = await API.request('/api/tasks');
        } else {
            const activeProjExists = State.projects.some(p => p.id == State.activeFilters.project);
            if (!activeProjExists) {
                State.activeFilters.project = 'all';
                document.getElementById('filter-project').value = 'all';
                tasks = await API.request('/api/tasks');
            } else {
                tasks = await API.request(`/api/projects/${State.activeFilters.project}/tasks`);
            }
        }

        let filtered = tasks;
        if (State.activeFilters.priority !== 'all') {
            filtered = filtered.filter(t => t.priority === State.activeFilters.priority);
        }
        if (State.activeFilters.status !== 'all') {
            filtered = filtered.filter(t => t.status === State.activeFilters.status);
        }

        todoCards.innerHTML = '';
        progressCards.innerHTML = '';
        doneCards.innerHTML = '';

        let counts = { Todo: 0, 'In Progress': 0, Done: 0 };

        filtered.forEach(task => {
            counts[task.status]++;

            const card = document.createElement('div');
            card.className = 'task-card';
            
            let initials = 'U';
            let name = 'Unassigned';
            if (task.assignee) {
                name = task.assignee.name;
                const parts = name.split(' ');
                initials = parts.map(p => p[0]).join('').substring(0,2).toUpperCase();
            }

            let isOverdue = false;
            let dateText = task.due_date || 'No due date';
            if (task.due_date && task.status !== 'Done') {
                const due = new Date(task.due_date);
                const today = new Date();
                today.setHours(0,0,0,0);
                if (due < today) {
                    isOverdue = true;
                }
            }

            const priorityBadge = `<span class="badge-priority badge-${task.priority.toLowerCase()}">${task.priority}</span>`;

            card.innerHTML = `
                <div class="task-card-header">
                    <span class="task-card-title">${task.title}</span>
                    ${priorityBadge}
                </div>
                <p class="task-card-desc">${task.description || 'No specifications provided.'}</p>
                <div class="task-card-meta">
                    <div class="task-card-date ${isOverdue ? 'overdue' : ''}">
                        <i data-lucide="calendar"></i>
                        <span>${dateText}</span>
                    </div>
                    <div class="task-card-assignee" title="Assignee: ${name}">
                        ${initials}
                    </div>
                </div>
            `;

            card.addEventListener('click', () => openTaskDetailsModal(task));

            if (task.status === 'Todo') todoCards.appendChild(card);
            if (task.status === 'In Progress') progressCards.appendChild(card);
            if (task.status === 'Done') doneCards.appendChild(card);
        });

        document.getElementById('badge-todo').innerText = counts['Todo'];
        document.getElementById('badge-progress').innerText = counts['In Progress'];
        document.getElementById('badge-done').innerText = counts['Done'];

        const columnData = [
            { el: todoCards, count: counts['Todo'], label: 'Todo' },
            { el: progressCards, count: counts['In Progress'], label: 'In Progress' },
            { el: doneCards, count: counts['Done'], label: 'Completed' }
        ];

        columnData.forEach(col => {
            if (col.count === 0) {
                col.el.innerHTML = `
                    <div class="empty-state" style="padding: 1.5rem">
                        <i data-lucide="check-square" style="width: 28px; height: 28px;"></i>
                        <p style="font-size:0.75rem">No ${col.label} tasks</p>
                    </div>
                `;
            }
        });

        lucide.createIcons();

    } catch (err) {
        showToast('Failed to load Kanban tasks.', 'error');
    }
}

// --- TASK DETAILS MODAL INJECTION & DISPLAY ---
async function openTaskDetailsModal(task) {
    document.getElementById('edit-task-id').value = task.id;

    // Resolve project name
    let project = State.projects.find(p => p.id === task.project_id);
    if (!project) {
        try {
            project = await API.request(`/api/projects/${task.project_id}`);
        } catch (e) {
            project = { name: `Project Portfolio #${task.project_id}` };
        }
    }
    
    document.getElementById('edit-task-project-name').innerHTML = `
        <span class="badge-status badge-todo">${project.name}</span>
    `;

    document.getElementById('edit-task-status').value = task.status;

    // Load read-only display values
    document.getElementById('edit-task-title-display').innerText = task.title;
    document.getElementById('edit-task-desc-display').innerText = task.description || 'No description provided.';
    
    let priColor = 'low';
    if (task.priority === 'Medium') priColor = 'medium';
    if (task.priority === 'High') priColor = 'high';
    
    document.getElementById('edit-task-priority-display').innerHTML = `
        <span class="badge-priority badge-${priColor}">${task.priority}</span>
    `;
    
    document.getElementById('edit-task-due-display').innerText = task.due_date || 'No target due date';
    document.getElementById('edit-task-assignee-display').innerText = task.assignee ? task.assignee.name : 'Unassigned';

    window.openModal('modal-task-details');
}

// --- 4. RENDER TEAM MEMBERS VIEW ---
async function renderMembers() {
    const container = document.getElementById('members-container');
    container.innerHTML = '<div class="text-center py-5 text-secondary">Retrieving user roster...</div>';

    try {
        const users = await API.request('/api/users');
        State.users = users;

        container.innerHTML = '';

        users.forEach(user => {
            const card = document.createElement('div');
            card.className = 'member-card';

            const parts = user.name.split(' ');
            const initials = parts.map(p => p[0]).join('').substring(0, 2).toUpperCase();

            card.innerHTML = `
                <div class="user-avatar">${initials}</div>
                <div class="member-details">
                    <h3>${user.name}</h3>
                    <p class="text-secondary">${user.email}</p>
                    <span class="user-role-badge ${user.role === 'Admin' ? 'admin' : ''}">${user.role}</span>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (err) {
        container.innerHTML = '<div class="text-center py-5 text-danger">Failed to load member portfolio.</div>';
    }
}

// --- Task Editor Submission (Status update only) ---
async function handleTaskEditSubmit(e) {
    e.preventDefault();
    const taskId = document.getElementById('edit-task-id').value;
    const status = document.getElementById('edit-task-status').value;

    try {
        await API.request(`/api/tasks/${taskId}`, {
            method: 'PUT',
            body: { status }
        });

        showToast('Task status updated successfully.');
        window.closeModal('modal-task-details');
        
        const baseHash = window.location.hash.split('?')[0];
        if (baseHash === '#dashboard') {
            renderDashboard();
        } else {
            renderTasks();
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}
