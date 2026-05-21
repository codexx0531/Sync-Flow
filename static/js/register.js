/* ==========================================
   SyncFlow Register JavaScript Logic
   ========================================== */

const API = {
    async request(url, options = {}) {
        options.credentials = 'include';
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

    setTimeout(() => {
        toast.style.transition = 'all 0.5s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 500);
    }, 3500);
}

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();

    const form = document.getElementById('register-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value.trim();
        const email = document.getElementById('auth-email').value.trim();
        const password = document.getElementById('auth-password').value;
        const role = document.getElementById('reg-role').value;

        try {
            const response = await API.request('/api/auth/signup', {
                method: 'POST',
                body: { name, email, password, role }
            });

            showToast('Account registered successfully! Redirecting...');
            
            setTimeout(() => {
                window.location.href = '/';
            }, 800);

        } catch (err) {
            showToast(err.message, 'error');
        }
    });
});
