import { databaseManager } from './database';
class DataManager {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000;
        this.subscribers = new Map();
        this.initializeEventListeners();
    }
    initializeEventListeners() {
        document.addEventListener('salesUpdated', () => this.notifySubscribers('sales'));
        document.addEventListener('inventoryUpdated', () => this.notifySubscribers('inventory'));
        document.addEventListener('recipesUpdated', () => this.notifySubscribers('recipes'));
    }
    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }
    getCache(key) {
        const cached = this.cache.get(key);
        if (!cached)
            return null;
        if (Date.now() - cached.timestamp > this.cacheTimeout) {
            this.cache.delete(key);
            return null;
        }
        return cached.data;
    }
    clearCache(key) {
        if (key) {
            this.cache.delete(key);
        }
        else {
            this.cache.clear();
        }
    }
    subscribe(event, callback) {
        if (!this.subscribers.has(event)) {
            this.subscribers.set(event, []);
        }
        this.subscribers.get(event).push(callback);
    }
    unsubscribe(event, callback) {
        const callbacks = this.subscribers.get(event);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    notifySubscribers(event) {
        const callbacks = this.subscribers.get(event);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback();
                }
                catch (error) {
                    console.error(`Error in subscriber callback for ${event}:`, error);
                }
            });
        }
    }
    async loadSales() {
        const cacheKey = 'sales';
        const cached = this.getCache(cacheKey);
        if (cached)
            return cached;
        try {
            const response = await databaseManager.getSales({
                orderBy: { column: 'date', ascending: false },
                limit: 100
            });
            if (response.success && response.data) {
                this.setCache(cacheKey, response.data);
                return response.data;
            }
            else {
                console.error('Error loading sales:', response.error);
                return [];
            }
        }
        catch (error) {
            console.error('Exception loading sales:', error);
            return [];
        }
    }
    async addSale(saleData) {
        try {
            const sale = {
                ...saleData,
                date: new Date(),
                total: saleData.quantity * saleData.price
            };
            const response = await databaseManager.addSale(sale);
            if (response.success) {
                this.clearCache('sales');
                this.notifySubscribers('sales');
                await this.updateInventoryFromSale(saleData.productName, saleData.quantity);
            }
            return response;
        }
        catch (error) {
            console.error('Error adding sale:', error);
            return { success: false, error: error.message };
        }
    }
    async updateSale(id, updates) {
        try {
            const response = await databaseManager.updateSale(id, updates);
            if (response.success) {
                this.clearCache('sales');
                this.notifySubscribers('sales');
            }
            return response;
        }
        catch (error) {
            console.error('Error updating sale:', error);
            return { success: false, error: error.message };
        }
    }
    async deleteSale(id) {
        try {
            const response = await databaseManager.deleteSale(id);
            if (response.success) {
                this.clearCache('sales');
                this.notifySubscribers('sales');
            }
            return response;
        }
        catch (error) {
            console.error('Error deleting sale:', error);
            return { success: false, error: error.message };
        }
    }
    async loadInventory() {
        const cacheKey = 'inventory';
        const cached = this.getCache(cacheKey);
        if (cached)
            return cached;
        try {
            const response = await databaseManager.getInventory({
                orderBy: { column: 'name', ascending: true }
            });
            if (response.success && response.data) {
                this.setCache(cacheKey, response.data);
                return response.data;
            }
            else {
                console.error('Error loading inventory:', response.error);
                return [];
            }
        }
        catch (error) {
            console.error('Exception loading inventory:', error);
            return [];
        }
    }
    async addInventory(item) {
        try {
            const response = await databaseManager.addInventory(item);
            if (response.success) {
                this.clearCache('inventory');
                this.notifySubscribers('inventory');
            }
            return response;
        }
        catch (error) {
            console.error('Error adding inventory:', error);
            return { success: false, error: error.message };
        }
    }
    async updateInventory(id, updates) {
        try {
            const response = await databaseManager.updateInventory(id, updates);
            if (response.success) {
                this.clearCache('inventory');
                this.notifySubscribers('inventory');
            }
            return response;
        }
        catch (error) {
            console.error('Error updating inventory:', error);
            return { success: false, error: error.message };
        }
    }
    async deleteInventory(id) {
        try {
            const response = await databaseManager.deleteInventory(id);
            if (response.success) {
                this.clearCache('inventory');
                this.notifySubscribers('inventory');
            }
            return response;
        }
        catch (error) {
            console.error('Error deleting inventory:', error);
            return { success: false, error: error.message };
        }
    }
    async updateInventoryFromSale(productName, quantitySold) {
        try {
            const inventory = await this.loadInventory();
            const item = inventory.find(inv => inv.name.toLowerCase() === productName.toLowerCase());
            if (item) {
                const newQuantity = Math.max(0, item.quantity - quantitySold);
                await this.updateInventory(item.id, { quantity: newQuantity });
            }
        }
        catch (error) {
            console.error('Error updating inventory from sale:', error);
        }
    }
    async loadRecipes() {
        const cacheKey = 'recipes';
        const cached = this.getCache(cacheKey);
        if (cached)
            return cached;
        try {
            const response = await databaseManager.getRecipes({
                orderBy: { column: 'name', ascending: true }
            });
            if (response.success && response.data) {
                this.setCache(cacheKey, response.data);
                return response.data;
            }
            else {
                console.error('Error loading recipes:', response.error);
                return [];
            }
        }
        catch (error) {
            console.error('Exception loading recipes:', error);
            return [];
        }
    }
    async addRecipe(recipe) {
        try {
            const response = await databaseManager.addRecipe(recipe);
            if (response.success) {
                this.clearCache('recipes');
                this.notifySubscribers('recipes');
            }
            return response;
        }
        catch (error) {
            console.error('Error adding recipe:', error);
            return { success: false, error: error.message };
        }
    }
    async updateRecipe(id, updates) {
        try {
            const response = await databaseManager.updateRecipe(id, updates);
            if (response.success) {
                this.clearCache('recipes');
                this.notifySubscribers('recipes');
            }
            return response;
        }
        catch (error) {
            console.error('Error updating recipe:', error);
            return { success: false, error: error.message };
        }
    }
    async deleteRecipe(id) {
        try {
            const response = await databaseManager.deleteRecipe(id);
            if (response.success) {
                this.clearCache('recipes');
                this.notifySubscribers('recipes');
            }
            return response;
        }
        catch (error) {
            console.error('Error deleting recipe:', error);
            return { success: false, error: error.message };
        }
    }
    async loadSettings() {
        const cacheKey = 'settings';
        const cached = this.getCache(cacheKey);
        if (cached)
            return cached;
        try {
            const savedSettings = localStorage.getItem('stockZeroSettings');
            const settings = savedSettings ? JSON.parse(savedSettings) : {
                theme: 'light',
                currency: 'USD',
                language: 'es',
                notifications: true,
                autoBackup: true,
                backupInterval: 24
            };
            this.setCache(cacheKey, settings);
            return settings;
        }
        catch (error) {
            console.error('Error loading settings:', error);
            return {
                theme: 'light',
                currency: 'USD',
                language: 'es',
                notifications: true,
                autoBackup: true,
                backupInterval: 24
            };
        }
    }
    async saveSettings(settings) {
        try {
            localStorage.setItem('stockZeroSettings', JSON.stringify(settings));
            this.setCache('settings', settings);
            return { success: true, data: settings };
        }
        catch (error) {
            console.error('Error saving settings:', error);
            return { success: false, error: error.message };
        }
    }
    async getSalesReport(startDate, endDate) {
        try {
            const sales = await this.loadSales();
            const filteredSales = sales.filter(sale => sale.date >= startDate && sale.date <= endDate);
            const totalSales = filteredSales.length;
            const totalRevenue = filteredSales.reduce((sum, sale) => sum + sale.total, 0);
            const averageOrderValue = totalSales > 0 ? totalRevenue / totalSales : 0;
            const productSales = new Map();
            filteredSales.forEach(sale => {
                const existing = productSales.get(sale.productName) || { quantity: 0, revenue: 0 };
                productSales.set(sale.productName, {
                    quantity: existing.quantity + sale.quantity,
                    revenue: existing.revenue + sale.total
                });
            });
            const topProducts = Array.from(productSales.entries())
                .sort(([, a], [, b]) => b.revenue - a.revenue)
                .slice(0, 5)
                .map(([name, data]) => ({
                id: '',
                productName: name,
                quantity: data.quantity,
                price: data.revenue / data.quantity,
                total: data.revenue,
                date: new Date()
            }));
            const dailySalesMap = new Map();
            filteredSales.forEach(sale => {
                const dateKey = sale.date.toISOString().split('T')[0];
                const existing = dailySalesMap.get(dateKey) || { sales: 0, revenue: 0 };
                dailySalesMap.set(dateKey, {
                    sales: existing.sales + 1,
                    revenue: existing.revenue + sale.total
                });
            });
            const dailySales = Array.from(dailySalesMap.entries())
                .map(([date, data]) => ({ date, ...data }))
                .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
            return {
                totalSales,
                totalRevenue,
                averageOrderValue,
                topProducts,
                dailySales
            };
        }
        catch (error) {
            console.error('Error generating sales report:', error);
            return {
                totalSales: 0,
                totalRevenue: 0,
                averageOrderValue: 0,
                topProducts: [],
                dailySales: []
            };
        }
    }
    async getInventoryReport() {
        try {
            const inventory = await this.loadInventory();
            const totalItems = inventory.length;
            const lowStockItems = inventory.filter(item => item.quantity <= item.minQuantity).length;
            const totalValue = inventory.reduce((sum, item) => sum + (item.quantity * item.cost), 0);
            const categoryMap = new Map();
            inventory.forEach(item => {
                const existing = categoryMap.get(item.category) || { count: 0, value: 0 };
                categoryMap.set(item.category, {
                    count: existing.count + 1,
                    value: existing.value + (item.quantity * item.cost)
                });
            });
            const itemsByCategory = Array.from(categoryMap.entries())
                .map(([category, data]) => ({ category, ...data }))
                .sort((a, b) => b.value - a.value);
            return {
                totalItems,
                lowStockItems,
                totalValue,
                itemsByCategory
            };
        }
        catch (error) {
            console.error('Error generating inventory report:', error);
            return {
                totalItems: 0,
                lowStockItems: 0,
                totalValue: 0,
                itemsByCategory: []
            };
        }
    }
    validateSaleData(data) {
        const errors = [];
        if (!data.productName || typeof data.productName !== 'string') {
            errors.push('Product name is required');
        }
        if (!data.quantity || typeof data.quantity !== 'number' || data.quantity <= 0) {
            errors.push('Quantity must be a positive number');
        }
        if (!data.price || typeof data.price !== 'number' || data.price <= 0) {
            errors.push('Price must be a positive number');
        }
        return {
            isValid: errors.length === 0,
            errors
        };
    }
    validateInventoryData(data) {
        const errors = [];
        if (!data.name || typeof data.name !== 'string') {
            errors.push('Item name is required');
        }
        if (typeof data.quantity !== 'number' || data.quantity < 0) {
            errors.push('Quantity must be a non-negative number');
        }
        if (typeof data.minQuantity !== 'number' || data.minQuantity < 0) {
            errors.push('Minimum quantity must be a non-negative number');
        }
        if (typeof data.maxQuantity !== 'number' || data.maxQuantity < data.minQuantity) {
            errors.push('Maximum quantity must be greater than or equal to minimum quantity');
        }
        if (!data.unit || typeof data.unit !== 'string') {
            errors.push('Unit is required');
        }
        if (!data.category || typeof data.category !== 'string') {
            errors.push('Category is required');
        }
        if (typeof data.cost !== 'number' || data.cost < 0) {
            errors.push('Cost must be a non-negative number');
        }
        return {
            isValid: errors.length === 0,
            errors
        };
    }
    async exportData(type) {
        try {
            let data = [];
            switch (type) {
                case 'sales':
                    data = await this.loadSales();
                    break;
                case 'inventory':
                    data = await this.loadInventory();
                    break;
                case 'recipes':
                    data = await this.loadRecipes();
                    break;
            }
            const csv = this.convertToCSV(data);
            return csv;
        }
        catch (error) {
            console.error(`Error exporting ${type}:`, error);
            return '';
        }
    }
    convertToCSV(data) {
        if (data.length === 0)
            return '';
        const headers = Object.keys(data[0]);
        const csvHeaders = headers.join(',');
        const csvRows = data.map(row => headers.map(header => {
            const value = row[header];
            return typeof value === 'string' && value.includes(',')
                ? `"${value}"`
                : value;
        }).join(','));
        return [csvHeaders, ...csvRows].join('\n');
    }
}
const dataManager = new DataManager();
export { DataManager, dataManager };
window.dataManager = dataManager;
//# sourceMappingURL=data-management.js.map