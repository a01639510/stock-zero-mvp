// Stock Zero - Main Application TypeScript

import { AppState, User, Session, TabType, Settings } from './types';

// Global State
const appState: AppState = {
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

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp(): void {
    console.log('Initializing Stock Zero App...');
    
    // Check for saved session
    const savedSession = localStorage.getItem('stockZeroSession');
    if (savedSession) {
        try {
            const session: Session = JSON.parse(savedSession);
            if (session.expiresAt > Date.now()) {
                appState.user = session.user;
                appState.isAuthenticated = true;
                showMainApp();
            } else {
                localStorage.removeItem('stockZeroSession');
            }
        } catch (error) {
            console.error('Error parsing session:', error);
            localStorage.removeItem('stockZeroSession');
        }
    }
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Hide loading screen
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

function initializeEventListeners(): void {
    // Navigation
    const navButtons = document.querySelectorAll('[data-tab]');
    navButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const target = e.target as HTMLElement;
            const tab = target.dataset.tab as TabType;
            if (tab) {
                switchTab(tab);
            }
        });
    });
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Settings form
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsUpdate);
    }
}

function handleLogin(event: Event): void {
    event.preventDefault();
    
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);
    
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    
    if (!email || !password) {
        showError('Por favor complete todos los campos');
        return;
    }
    
    // Simulate authentication (replace with real auth)
    const user: User = {
        id: '1',
        email: email,
        name: email.split('@')[0],
        role: 'admin',
        createdAt: new Date()
    };
    
    const session: Session = {
        user: user,
        token: Math.random().toString(36).substr(2, 9),
        expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
    };
    
    localStorage.setItem('stockZeroSession', JSON.stringify(session));
    appState.user = user;
    appState.isAuthenticated = true;
    
    showMainApp();
}

function handleLogout(): void {
    localStorage.removeItem('stockZeroSession');
    localStorage.removeItem('user_id');
    appState.user = null;
    appState.isAuthenticated = false;
    
    const mainApp = document.getElementById('mainApp');
    const loginScreen = document.getElementById('loginScreen');
    
    if (mainApp) mainApp.classList.add('hidden');
    if (loginScreen) loginScreen.classList.remove('hidden');
}

function showMainApp(): void {
    const loginScreen = document.getElementById('loginScreen');
    const mainApp = document.getElementById('mainApp');
    
    if (loginScreen) loginScreen.classList.add('hidden');
    if (mainApp) mainApp.classList.remove('hidden');
    
    // Load initial data
    loadDashboardData();
}

function switchTab(tabName: TabType): void {
    appState.currentTab = tabName;
    
    // Update UI
    document.querySelectorAll('[data-tab]').forEach(el => {
        el.classList.remove('bg-blue-600', 'text-white');
        el.classList.add('text-gray-600', 'hover:bg-gray-100');
    });
    
    const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.remove('text-gray-600', 'hover:bg-gray-100');
        activeTab.classList.add('bg-blue-600', 'text-white');
    }
    
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}Tab`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName: TabType): void {
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

function loadDashboardData(): void {
    // This will be implemented in other modules
    if (typeof window.loadDashboardKPIs === 'function') {
        window.loadDashboardKPIs();
    }
}

function loadInventoryData(): void {
    if (typeof window.loadInventoryList === 'function') {
        window.loadInventoryList();
    }
}

function loadSalesData(): void {
    if (typeof window.loadSalesList === 'function') {
        window.loadSalesList();
    }
}

function loadRecipesData(): void {
    if (typeof window.loadRecipesList === 'function') {
        window.loadRecipesList();
    }
}

function loadAnalyticsData(): void {
    if (typeof window.loadAnalyticsCharts === 'function') {
        window.loadAnalyticsCharts();
    }
}

function loadSettingsData(): void {
    // Load current settings into form
    const settingsForm = document.getElementById('settingsForm') as HTMLFormElement;
    if (settingsForm) {
        const formData = appState.data.settings;
        Object.keys(formData).forEach(key => {
            const input = settingsForm.elements.namedItem(key) as HTMLInputElement;
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = formData[key as keyof Settings] as boolean;
                } else {
                    input.value = formData[key as keyof Settings] as string;
                }
            }
        });
    }
}

function handleSettingsUpdate(event: Event): void {
    event.preventDefault();
    
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);
    
    const newSettings: Settings = {
        theme: formData.get('theme') as 'light' | 'dark',
        currency: formData.get('currency') as string,
        language: formData.get('language') as string,
        notifications: formData.get('notifications') === 'on',
        autoBackup: formData.get('autoBackup') === 'on',
        backupInterval: parseInt(formData.get('backupInterval') as string)
    };
    
    appState.data.settings = newSettings;
    localStorage.setItem('stockZeroSettings', JSON.stringify(newSettings));
    
    showSuccess('Configuración guardada exitosamente');
}

function showError(message: string): void {
    // Create and show error notification
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showSuccess(message: string): void {
    // Create and show success notification
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Export functions for use in other modules
declare global {
    interface Window {
        appState: AppState;
        initializeApp: typeof initializeApp;
        switchTab: typeof switchTab;
        showError: typeof showError;
        showSuccess: typeof showSuccess;
    }
}

window.appState = appState;
window.initializeApp = initializeApp;
window.switchTab = switchTab;
window.showError = showError;
window.showSuccess = showSuccess;