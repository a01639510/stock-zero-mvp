// Stock Zero - Main Application JavaScript

// Global State
const appState = {
    user: null,
    isAuthenticated: false,
    currentTab: 'dashboard',
    data: {
        sales: [],
        inventory: [],
        recipes: [],
        settings: {}
    },
    kpis: {},
    loading: false
};

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('Initializing Stock Zero App...');
    
    // Check for saved session
    const savedSession = localStorage.getItem('stockZeroSession');
    if (savedSession) {
        const session = JSON.parse(savedSession);
        if (session.expiresAt > Date.now()) {
            appState.user = session.user;
            appState.isAuthenticated = true;
            showMainApp();
        } else {
            localStorage.removeItem('stockZeroSession');
        }
    }
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Hide loading screen
    setTimeout(() => {
        document.getElementById('loadingScreen').classList.add('hidden');
        
        if (!appState.isAuthenticated) {
            document.getElementById('loginScreen').classList.remove('hidden');
        }
    }, 1000);
}

function initializeEventListeners() {
    // File upload listeners
    document.getElementById('salesFile')?.addEventListener('change', handleFileUpload);
    document.getElementById('inventoryFile')?.addEventListener('change', handleFileUpload);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Auto-sync timer
    setInterval(autoSync, 5 * 60 * 1000); // Sync every 5 minutes
}

function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + S: Save/Export
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        exportData('current');
    }
    
    // Escape: Close modals
    if (event.key === 'Escape') {
        closeAllModals();
    }
}

// Authentication Functions
function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    // Show loading state
    const submitButton = event.target.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Iniciando sesión...';
    submitButton.disabled = true;
    
    // Simulate authentication (replace with real auth)
    setTimeout(() => {
        // Mock authentication
        if (email && password) {
            appState.user = { email: email, name: email.split('@')[0] };
            appState.isAuthenticated = true;
            
            // Save session
            const session = {
                user: appState.user,
                expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
            };
            localStorage.setItem('stockZeroSession', JSON.stringify(session));
            
            showMainApp();
            showNotification('¡Bienvenido a Stock Zero!', 'success');
        } else {
            showNotification('Por favor, completa todos los campos', 'error');
        }
        
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }, 1500);
}

function handleLogout() {
    if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
        appState.user = null;
        appState.isAuthenticated = false;
        localStorage.removeItem('stockZeroSession');
        
        document.getElementById('mainApp').classList.add('hidden');
        document.getElementById('loginScreen').classList.remove('hidden');
        
        showNotification('Sesión cerrada correctamente', 'info');
    }
}

function loadDemoData() {
    showNotification('Cargando datos de demostración...', 'info');
    
    // Generate sample data
    const sampleData = generateSampleData();
    
    appState.data.sales = sampleData.sales;
    appState.data.inventory = sampleData.inventory;
    appState.data.recipes = sampleData.recipes;
    
    // Simulate successful login with demo user
    appState.user = { email: 'demo@stockzero.com', name: 'Demo User' };
    appState.isAuthenticated = true;
    
    const session = {
        user: appState.user,
        expiresAt: Date.now() + (24 * 60 * 60 * 1000)
    };
    localStorage.setItem('stockZeroSession', JSON.stringify(session));
    
    showMainApp();
    showNotification('Datos de demo cargados exitosamente', 'success');
}

function showMainApp() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    
    // Update user display
    document.getElementById('userEmail').textContent = appState.user.email;
    
    // Initialize dashboard
    loadDashboard();
    
    // Load data from localStorage if available
    loadSavedData();
}

// Tab Navigation
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600');
        button.classList.add('text-gray-500');
    });
    
    const activeTabButton = document.getElementById(tabName + 'Tab');
    if (activeTabButton) {
        activeTabButton.classList.remove('text-gray-500');
        activeTabButton.classList.add('text-blue-600', 'border-b-2', 'border-blue-600');
    }
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    const activeContent = document.getElementById(tabName + 'Content');
    if (activeContent) {
        activeContent.classList.remove('hidden');
    }
    
    appState.currentTab = tabName;
    
    // Load tab-specific data
    switch (tabName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'analysis':
            loadAnalysis();
            break;
        case 'optimization':
            loadOptimization();
            break;
        case 'data':
            loadDataManagement();
            break;
        case 'recipes':
            loadRecipes();
            break;
    }
    
    // Save current tab
    localStorage.setItem('stockZeroCurrentTab', tabName);
}

// Dashboard Functions
function loadDashboard() {
    if (appState.loading) return;
    
    appState.loading = true;
    showLoadingState('dashboardContent');
    
    // Calculate KPIs
    calculateKPIs();
    
    // Load KPI cards
    loadKPICards();
    
    // Load charts
    loadSalesTrendChart();
    loadInventoryStatusChart();
    
    // Load recent activity
    loadRecentActivity();
    
    // Check for critical products
    checkCriticalProducts();
    
    setTimeout(() => {
        appState.loading = false;
        hideLoadingState('dashboardContent');
    }, 1000);
}

function calculateKPIs() {
    const sales = appState.data.sales;
    const inventory = appState.data.inventory;
    
    if (sales.length === 0) {
        appState.kpis = {
            totalSales: 0,
            salesGrowth: 0,
            criticalProducts: 0,
            efficiency: 0,
            inventoryValue: 0
        };
        return;
    }
    
    // Calculate total sales
    const totalSales = sales.reduce((sum, sale) => sum + parseFloat(sale.ventas || 0), 0);
    
    // Calculate sales growth (last 30 days vs previous 30 days)
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    const sixtyDaysAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);
    
    const recentSales = sales.filter(sale => new Date(sale.fecha) >= thirtyDaysAgo)
        .reduce((sum, sale) => sum + parseFloat(sale.ventas || 0), 0);
    const previousSales = sales.filter(sale => {
        const saleDate = new Date(sale.fecha);
        return saleDate >= sixtyDaysAgo && saleDate < thirtyDaysAgo;
    }).reduce((sum, sale) => sum + parseFloat(sale.ventas || 0), 0);
    
    const salesGrowth = previousSales > 0 ? ((recentSales - previousSales) / previousSales * 100) : 0;
    
    // Calculate critical products
    const criticalProducts = inventory.filter(item => 
        parseFloat(item.stock_actual || 0) <= parseFloat(item.stock_minimo || 0)
    ).length;
    
    // Calculate efficiency (mock calculation)
    const efficiency = Math.min(95, Math.max(75, 85 + Math.random() * 10));
    
    // Calculate inventory value
    const inventoryValue = inventory.reduce((sum, item) => 
        sum + (parseFloat(item.stock_actual || 0) * 10), // Assume $10 per unit
    0);
    
    appState.kpis = {
        totalSales,
        salesGrowth,
        criticalProducts,
        efficiency,
        inventoryValue
    };
}

function loadKPICards() {
    const container = document.getElementById('kpiCards');
    const kpis = appState.kpis;
    
    const kpiCards = [
        {
            title: 'Ventas Totales',
            value: formatCurrency(kpis.totalSales),
            change: kpis.salesGrowth,
            icon: 'fa-chart-line',
            color: 'blue'
        },
        {
            title: 'Productos Críticos',
            value: kpis.criticalProducts.toString(),
            change: kpis.criticalProducts > 0 ? -kpis.criticalProducts : 0,
            icon: 'fa-exclamation-triangle',
            color: kpis.criticalProducts > 0 ? 'red' : 'green'
        },
        {
            title: 'Eficiencia Operativa',
            value: kpis.efficiency.toFixed(1) + '%',
            change: kpis.efficiency - 85,
            icon: 'fa-tachometer-alt',
            color: 'green'
        },
        {
            title: 'Valor del Inventario',
            value: formatCurrency(kpis.inventoryValue),
            change: -5.2,
            icon: 'fa-boxes',
            color: 'orange'
        }
    ];
    
    container.innerHTML = kpiCards.map(kpi => createKPICard(kpi)).join('');
}

function createKPICard(kpi) {
    const changeClass = kpi.change >= 0 ? 'positive' : 'negative';
    const changeSymbol = kpi.change >= 0 ? '+' : '';
    const changeColor = kpi.change >= 0 ? 'text-green-600' : 'text-red-600';
    
    return `
        <div class="kpi-card">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 bg-${kpi.color}-100 rounded-lg flex items-center justify-center">
                    <i class="fas ${kpi.icon} text-${kpi.color}-600 text-xl"></i>
                </div>
                <span class="kpi-change ${changeClass}">
                    <i class="fas fa-arrow-${kpi.change >= 0 ? 'up' : 'down'} mr-1"></i>
                    ${changeSymbol}${Math.abs(kpi.change).toFixed(1)}%
                </span>
            </div>
            <h3 class="kpi-label">${kpi.title}</h3>
            <p class="kpi-value">${kpi.value}</p>
        </div>
    `;
}

function loadSalesTrendChart() {
    const container = document.getElementById('salesTrendChart');
    const sales = appState.data.sales;
    
    if (sales.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No hay datos de ventas disponibles</p>';
        return;
    }
    
    // Group sales by date
    const dailySales = {};
    sales.forEach(sale => {
        const date = sale.fecha.split('T')[0]; // Extract date part
        dailySales[date] = (dailySales[date] || 0) + parseFloat(sale.ventas || 0);
    });
    
    const sortedDates = Object.keys(dailySales).sort();
    const trace = {
        x: sortedDates,
        y: sortedDates.map(date => dailySales[date]),
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#3B82F6', width: 3 },
        marker: { color: '#3B82F6', size: 6 },
        name: 'Ventas Diarias',
        fill: 'tozeroy',
        fillcolor: 'rgba(59, 130, 246, 0.1)'
    };
    
    const layout = {
        title: '',
        showlegend: false,
        xaxis: { title: 'Fecha' },
        yaxis: { title: 'Ventas ($)', tickformat: '$,.0f' },
        template: 'plotly_white',
        margin: { t: 20, b: 40, l: 60, r: 20 },
        height: 300
    };
    
    Plotly.newPlot(container, [trace], layout, { responsive: true });
}

function loadInventoryStatusChart() {
    const container = document.getElementById('inventoryStatusChart');
    const inventory = appState.data.inventory;
    
    if (inventory.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No hay datos de inventario disponibles</p>';
        return;
    }
    
    const products = inventory.map(item => item.producto);
    const currentStock = inventory.map(item => parseFloat(item.stock_actual || 0));
    const minStock = inventory.map(item => parseFloat(item.stock_minimo || 0));
    const optimalStock = inventory.map(item => parseFloat(item.stock_optimo || 0));
    
    const colors = currentStock.map((stock, index) => 
        stock <= minStock[index] ? '#EF4444' : stock >= optimalStock[index] ? '#10B981' : '#F59E0B'
    );
    
    const currentTrace = {
        x: products,
        y: currentStock,
        type: 'bar',
        name: 'Stock Actual',
        marker: { 
            color: colors,
            line: { color: 'rgba(255,255,255,0.8)', width: 2 }
        }
    };
    
    const minTrace = {
        x: products,
        y: minStock,
        type: 'scatter',
        mode: 'lines',
        name: 'Stock Mínimo',
        line: { color: '#EF4444', width: 2, dash: 'dash' }
    };
    
    const optimalTrace = {
        x: products,
        y: optimalStock,
        type: 'scatter',
        mode: 'lines',
        name: 'Stock Óptimo',
        line: { color: '#10B981', width: 2, dash: 'dash' }
    };
    
    const layout = {
        title: '',
        showlegend: true,
        xaxis: { title: 'Productos' },
        yaxis: { title: 'Cantidad' },
        template: 'plotly_white',
        margin: { t: 20, b: 40, l: 60, r: 20 },
        height: 300,
        legend: { x: 0.7, y: 0.95 }
    };
    
    Plotly.newPlot(container, [currentTrace, minTrace, optimalTrace], layout, { responsive: true });
}

function loadRecentActivity() {
    const container = document.getElementById('recentActivity');
    
    // Mock activity data
    const activities = [
        { type: 'warning', message: 'Producto A tiene stock crítico', time: 'Hace 5 minutos' },
        { type: 'info', message: 'Optimización de pedidos completada', time: 'Hace 1 hora' },
        { type: 'success', message: 'Nueva venta registrada: Producto C x50', time: 'Hace 2 horas' },
        { type: 'warning', message: 'Producto B necesita reabastecimiento', time: 'Hace 3 horas' },
        { type: 'info', message: 'Sincronización de datos completada', time: 'Hace 4 horas' }
    ];
    
    container.innerHTML = activities.map(activity => createActivityItem(activity)).join('');
}

function createActivityItem(activity) {
    const iconClass = activity.type === 'warning' ? 'fa-exclamation-triangle text-yellow-600' :
                     activity.type === 'success' ? 'fa-check-circle text-green-600' :
                     'fa-info-circle text-blue-600';
    
    return `
        <div class="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <i class="fas ${iconClass}"></i>
            <div class="flex-1">
                <p class="text-sm font-medium text-gray-900">${activity.message}</p>
                <p class="text-xs text-gray-500">${activity.time}</p>
            </div>
        </div>
    `;
}

function checkCriticalProducts() {
    const criticalCount = appState.kpis.criticalProducts;
    const alertContainer = document.getElementById('criticalProductsAlert');
    
    if (criticalCount > 0) {
        alertContainer.classList.remove('hidden');
        alertContainer.querySelector('h4').textContent = 
            `¡${criticalCount} Producto${criticalCount > 1 ? 's' : ''} Crítico${criticalCount > 1 ? 's' : ''} Detectado${criticalCount > 1 ? 's' : ''}!`;
    } else {
        alertContainer.classList.add('hidden');
    }
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatNumber(value) {
    return new Intl.NumberFormat('es-MX').format(value);
}

function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notificationsContainer');
    const notification = document.createElement('div');
    
    const iconClass = type === 'success' ? 'fa-check-circle' :
                     type === 'warning' ? 'fa-exclamation-triangle' :
                     type === 'error' ? 'fa-times-circle' :
                     'fa-info-circle';
    
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${iconClass} mr-3"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(notification);
    
    // Auto remove
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out forwards';
        setTimeout(() => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        }, 300);
    }, duration);
}

function showLoadingState(containerId) {
    const container = document.getElementById(containerId);
    container.style.opacity = '0.5';
    container.style.pointerEvents = 'none';
}

function hideLoadingState(containerId) {
    const container = document.getElementById(containerId);
    container.style.opacity = '1';
    container.style.pointerEvents = 'auto';
}

function generateSampleData() {
    // Generate sample sales data
    const sales = [];
    const now = new Date();
    for (let i = 90; i >= 0; i--) {
        const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
        ['Producto A', 'Producto B', 'Producto C', 'Producto D', 'Producto E'].forEach(product => {
            sales.push({
                fecha: date.toISOString(),
                producto: product,
                ventas: Math.floor(Math.random() * 100) + 10,
                categoria: ['A', 'B', 'C'][Math.floor(Math.random() * 3)]
            });
        });
    }
    
    // Generate sample inventory data
    const inventory = [
        { producto: 'Producto A', stock_actual: 15, stock_minimo: 50, stock_optimo: 100 },
        { producto: 'Producto B', stock_actual: 8, stock_minimo: 25, stock_optimo: 60 },
        { producto: 'Producto C', stock_actual: 3, stock_minimo: 10, stock_optimo: 40 },
        { producto: 'Producto D', stock_actual: 156, stock_minimo: 100, stock_optimo: 150 },
        { producto: 'Producto E', stock_actual: 234, stock_minimo: 150, stock_optimo: 200 }
    ];
    
    // Generate sample recipes
    const recipes = [
        {
            id: 1,
            name: 'Receta Estándar',
            description: 'Receta base para producción',
            ingredients: [
                { name: 'Ingrediente A', quantity: 10, unit: 'kg' },
                { name: 'Ingrediente B', quantity: 5, unit: 'kg' },
                { name: 'Ingrediente C', quantity: 2, unit: 'L' }
            ],
            yield: 100,
            unit: 'unidades'
        },
        {
            id: 2,
            name: 'Receta Premium',
            description: 'Receta de alta calidad',
            ingredients: [
                { name: 'Ingrediente A', quantity: 15, unit: 'kg' },
                { name: 'Ingrediente B', quantity: 8, unit: 'kg' },
                { name: 'Ingrediente D', quantity: 3, unit: 'L' }
            ],
            yield: 80,
            unit: 'unidades'
        }
    ];
    
    return { sales, inventory, recipes };
}

// Settings Functions
function showSettings() {
    document.getElementById('settingsModal').classList.remove('hidden');
}

function closeSettings() {
    document.getElementById('settingsModal').classList.add('hidden');
}

function saveSettings() {
    showNotification('Configuración guardada exitosamente', 'success');
    closeSettings();
}

function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.add('hidden');
    });
}

// Sync Functions
function syncData() {
    showNotification('Sincronizando datos...', 'info');
    
    // Simulate sync
    setTimeout(() => {
        showNotification('Datos sincronizados exitosamente', 'success');
        if (appState.currentTab === 'dashboard') {
            loadDashboard();
        }
    }, 2000);
}

function autoSync() {
    if (appState.isAuthenticated) {
        syncData();
    }
}

// Data Persistence
function loadSavedData() {
    const savedData = localStorage.getItem('stockZeroData');
    if (savedData) {
        try {
            appState.data = JSON.parse(savedData);
        } catch (error) {
            console.error('Error loading saved data:', error);
        }
    }
}

function saveData() {
    localStorage.setItem('stockZeroData', JSON.stringify(appState.data));
}

// Initialize current tab from saved state
const savedTab = localStorage.getItem('stockZeroCurrentTab');
if (savedTab) {
    appState.currentTab = savedTab;
}