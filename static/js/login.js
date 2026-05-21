/* ==========================================
   SyncFlow Login JavaScript Logic
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

    // Check if seed credentials exist in localStorage from the welcome page
    const seedEmail = localStorage.getItem('seed_email');
    const seedPassword = localStorage.getItem('seed_password');
    if (seedEmail && seedPassword) {
        document.getElementById('auth-email').value = seedEmail;
        document.getElementById('auth-password').value = seedPassword;
        localStorage.removeItem('seed_email');
        localStorage.removeItem('seed_password');
        showToast('Seed account credentials loaded. Signing in...', 'success');
        
        // Auto-submit form after a short premium transition delay
        setTimeout(() => {
            document.getElementById('login-form').dispatchEvent(new Event('submit'));
        }, 800);
    }

    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('auth-email').value.trim();
        const password = document.getElementById('auth-password').value;

        try {
            const response = await API.request('/api/auth/login', {
                method: 'POST',
                body: { email, password }
            });

            showToast(`Welcome back, ${response.user.name}!`);
            
            // Redirect based on role
            setTimeout(() => {
                if (response.user.role === 'Admin' || response.user.role === 'Master') {
                    window.location.href = '/admin-dashboard';
                } else {
                    window.location.href = '/member-dashboard';
                }
            }, 800);

        } catch (err) {
            showToast(err.message, 'error');
        }
    });
});

window.setSeedAccount = function(email, password) {
    document.getElementById('auth-email').value = email;
    document.getElementById('auth-password').value = password;
    showToast('Seed account credentials loaded. Press Sign In.', 'info');
};
