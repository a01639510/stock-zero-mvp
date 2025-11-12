const appState = {
    user: null,
    isAuthenticated: false,
    currentTab: 'dashboard',
    data: {
        sales: [],
        inventory: [],
        recipes: [],
        settings: {
            theme: 'light',
            currency: 'USD',
            language: 'es',
            notifications: true,
            autoBackup: true,
            backupInterval: 24
        }
    },
    kpis: {},
    loading: false,
    error: null
};
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});
function initializeApp() {
    console.log('Initializing Stock Zero App...');
    const savedSession = localStorage.getItem('stockZeroSession');
    if (savedSession) {
        try {
            const session = JSON.parse(savedSession);
            if (session.expiresAt > Date.now()) {
                appState.user = session.user;
                appState.isAuthenticated = true;
                showMainApp();
            }
            else {
                localStorage.removeItem('stockZeroSession');
            }
        }
        catch (error) {
            console.error('Error parsing session:', error);
            localStorage.removeItem('stockZeroSession');
        }
    }
    initializeEventListeners();
    setTimeout(() => {
        const loadingScreen = document.getElementById('loadingScreen');
        const loginScreen = document.getElementById('loginScreen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
        }
        if (!appState.isAuthenticated && loginScreen) {
            loginScreen.classList.remove('hidden');
        }
    }, 1000);
}
function initializeEventListeners() {
    const navButtons = document.querySelectorAll('[data-tab]');
    navButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const target = e.target;
            const tab = target.dataset.tab;
            if (tab) {
                switchTab(tab);
            }
        });
    });
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsUpdate);
    }
}
function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const email = formData.get('email');
    const password = formData.get('password');
    if (!email || !password) {
        showError('Por favor complete todos los campos');
        return;
    }
    const user = {
        id: '1',
        email: email,
        name: email.split('@')[0],
        role: 'admin',
        createdAt: new Date()
    };
    const session = {
        user: user,
        token: Math.random().toString(36).substr(2, 9),
        expiresAt: Date.now() + (24 * 60 * 60 * 1000)
    };
    localStorage.setItem('stockZeroSession', JSON.stringify(session));
    appState.user = user;
    appState.isAuthenticated = true;
    showMainApp();
}
function handleLogout() {
    localStorage.removeItem('stockZeroSession');
    localStorage.removeItem('user_id');
    appState.user = null;
    appState.isAuthenticated = false;
    const mainApp = document.getElementById('mainApp');
    const loginScreen = document.getElementById('loginScreen');
    if (mainApp)
        mainApp.classList.add('hidden');
    if (loginScreen)
        loginScreen.classList.remove('hidden');
}
function showMainApp() {
    const loginScreen = document.getElementById('loginScreen');
    const mainApp = document.getElementById('mainApp');
    if (loginScreen)
        loginScreen.classList.add('hidden');
    if (mainApp)
        mainApp.classList.remove('hidden');
    loadDashboardData();
}
function switchTab(tabName) {
    appState.currentTab = tabName;
    document.querySelectorAll('[data-tab]').forEach(el => {
        el.classList.remove('bg-blue-600', 'text-white');
        el.classList.add('text-gray-600', 'hover:bg-gray-100');
    });
    const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.remove('text-gray-600', 'hover:bg-gray-100');
        activeTab.classList.add('bg-blue-600', 'text-white');
    }
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
    });
    const selectedTab = document.getElementById(`${tabName}Tab`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    loadTabData(tabName);
}
function loadTabData(tabName) {
    switch (tabName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'inventory':
            loadInventoryData();
            break;
        case 'sales':
            loadSalesData();
            break;
        case 'recipes':
            loadRecipesData();
            break;
        case 'analytics':
            loadAnalyticsData();
            break;
        case 'settings':
            loadSettingsData();
            break;
    }
}
function loadDashboardData() {
    if (typeof window.loadDashboardKPIs === 'function') {
        window.loadDashboardKPIs();
    }
}
function loadInventoryData() {
    if (typeof window.loadInventoryList === 'function') {
        window.loadInventoryList();
    }
}
function loadSalesData() {
    if (typeof window.loadSalesList === 'function') {
        window.loadSalesList();
    }
}
function loadRecipesData() {
    if (typeof window.loadRecipesList === 'function') {
        window.loadRecipesList();
    }
}
function loadAnalyticsData() {
    if (typeof window.loadAnalyticsCharts === 'function') {
        window.loadAnalyticsCharts();
    }
}
function loadSettingsData() {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        const formData = appState.data.settings;
        Object.keys(formData).forEach(key => {
            const input = settingsForm.elements.namedItem(key);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = formData[key];
                }
                else {
                    input.value = formData[key];
                }
            }
        });
    }
}
function handleSettingsUpdate(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const newSettings = {
        theme: formData.get('theme'),
        currency: formData.get('currency'),
        language: formData.get('language'),
        notifications: formData.get('notifications') === 'on',
        autoBackup: formData.get('autoBackup') === 'on',
        backupInterval: parseInt(formData.get('backupInterval'))
    };
    appState.data.settings = newSettings;
    localStorage.setItem('stockZeroSettings', JSON.stringify(newSettings));
    showSuccess('Configuración guardada exitosamente');
}
function showError(message) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
function showSuccess(message) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
window.appState = appState;
window.initializeApp = initializeApp;
window.switchTab = switchTab;
window.showError = showError;
window.showSuccess = showSuccess;
export {};
//# sourceMappingURL=app.js.map