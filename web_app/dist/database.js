class DatabaseManager {
    constructor() {
        this.supabaseUrl = null;
        this.supabaseKey = null;
        this.supabase = null;
        this.isConnected = false;
        this.connectionPromise = null;
    }
    async initialize() {
        if (this.connectionPromise)
            return this.connectionPromise;
        this.connectionPromise = this._connect();
        return this.connectionPromise;
    }
    async _connect() {
        try {
            const config = await this._loadConfig();
            if (config.supabaseUrl && config.supabaseKey) {
                this.supabaseUrl = config.supabaseUrl;
                this.supabaseKey = config.supabaseKey;
                console.log("✅ Database configuration found");
                this.isConnected = true;
                if (typeof window !== 'undefined' && window.supabase) {
                    this.supabase = window.supabase.createClient(this.supabaseUrl, this.supabaseKey);
                    console.log("✅ Supabase client initialized");
                }
            }
            else {
                console.warn("⚠️ No database configuration found, using local storage");
                this.isConnected = true;
            }
        }
        catch (error) {
            console.error("❌ Database connection error:", error);
            this.isConnected = false;
            throw error;
        }
    }
    async _loadConfig() {
        return new Promise((resolve) => {
            const supabaseUrl = process.env.SUPABASE_URL ||
                document.querySelector('meta[name="supabase-url"]')?.content ||
                localStorage.getItem('supabase_url');
            const supabaseKey = process.env.SUPABASE_KEY ||
                document.querySelector('meta[name="supabase-key"]')?.content ||
                localStorage.getItem('supabase_key');
            resolve({
                supabaseUrl: supabaseUrl || '',
                supabaseKey: supabaseKey || ''
            });
        });
    }
    async saveConfig(url, key) {
        localStorage.setItem('supabase_url', url);
        localStorage.setItem('supabase_key', key);
        this.supabaseUrl = url;
        this.supabaseKey = key;
        this.connectionPromise = null;
        await this.initialize();
    }
    async query(table, options = {}) {
        try {
            if (!this.isConnected) {
                await this.initialize();
            }
            if (this.supabase) {
                let query = this.supabase.from(table).select();
                if (options.filters) {
                    options.filters.forEach((filter) => {
                        query = query.filter(filter.column, filter.operator, filter.value);
                    });
                }
                if (options.orderBy) {
                    query = query.order(options.orderBy.column, {
                        ascending: options.orderBy.ascending !== false
                    });
                }
                if (options.limit) {
                    query = query.limit(options.limit);
                }
                const { data, error } = await query;
                if (error) {
                    console.error(`Query error for table ${table}:`, error);
                    return { success: false, error: error.message };
                }
                return { success: true, data };
            }
            else {
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                return { success: true, data };
            }
        }
        catch (error) {
            console.error(`Exception in query for table ${table}:`, error);
            return { success: false, error: error.message };
        }
    }
    async insert(table, record) {
        try {
            if (!this.isConnected) {
                await this.initialize();
            }
            if (this.supabase) {
                const { data, error } = await this.supabase
                    .from(table)
                    .insert([record])
                    .select()
                    .single();
                if (error) {
                    console.error(`Insert error for table ${table}:`, error);
                    return { success: false, error: error.message };
                }
                return { success: true, data };
            }
            else {
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                const newRecord = { ...record, id: this.generateId() };
                data.push(newRecord);
                localStorage.setItem(`stockzero_${table}`, JSON.stringify(data));
                return { success: true, data: newRecord };
            }
        }
        catch (error) {
            console.error(`Exception in insert for table ${table}:`, error);
            return { success: false, error: error.message };
        }
    }
    async update(table, id, updates) {
        try {
            if (!this.isConnected) {
                await this.initialize();
            }
            if (this.supabase) {
                const { data, error } = await this.supabase
                    .from(table)
                    .update(updates)
                    .eq('id', id)
                    .select()
                    .single();
                if (error) {
                    console.error(`Update error for table ${table}:`, error);
                    return { success: false, error: error.message };
                }
                return { success: true, data };
            }
            else {
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                const index = data.findIndex((item) => item.id === id);
                if (index !== -1) {
                    data[index] = { ...data[index], ...updates };
                    localStorage.setItem(`stockzero_${table}`, JSON.stringify(data));
                    return { success: true, data: data[index] };
                }
                return { success: false, error: 'Record not found' };
            }
        }
        catch (error) {
            console.error(`Exception in update for table ${table}:`, error);
            return { success: false, error: error.message };
        }
    }
    async delete(table, id) {
        try {
            if (!this.isConnected) {
                await this.initialize();
            }
            if (this.supabase) {
                const { error } = await this.supabase
                    .from(table)
                    .delete()
                    .eq('id', id);
                if (error) {
                    console.error(`Delete error for table ${table}:`, error);
                    return { success: false, error: error.message };
                }
                return { success: true };
            }
            else {
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                const filteredData = data.filter((item) => item.id !== id);
                localStorage.setItem(`stockzero_${table}`, JSON.stringify(filteredData));
                return { success: true };
            }
        }
        catch (error) {
            console.error(`Exception in delete for table ${table}:`, error);
            return { success: false, error: error.message };
        }
    }
    async getSales(options = {}) {
        return this.query('sales', options);
    }
    async addSale(sale) {
        return this.insert('sales', sale);
    }
    async updateSale(id, updates) {
        return this.update('sales', id, updates);
    }
    async deleteSale(id) {
        return this.delete('sales', id);
    }
    async getInventory(options = {}) {
        return this.query('inventory', options);
    }
    async addInventory(item) {
        const inventoryItem = {
            ...item,
            lastUpdated: new Date()
        };
        return this.insert('inventory', inventoryItem);
    }
    async updateInventory(id, updates) {
        return this.update('inventory', id, { ...updates, lastUpdated: new Date() });
    }
    async deleteInventory(id) {
        return this.delete('inventory', id);
    }
    async getRecipes(options = {}) {
        return this.query('recipes', options);
    }
    async addRecipe(recipe) {
        return this.insert('recipes', recipe);
    }
    async updateRecipe(id, updates) {
        return this.update('recipes', id, updates);
    }
    async deleteRecipe(id) {
        return this.delete('recipes', id);
    }
    generateId() {
        return Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }
    isReady() {
        return this.isConnected;
    }
    getConnectionStatus() {
        if (this.supabase)
            return 'supabase';
        if (this.isConnected)
            return 'local';
        return 'disconnected';
    }
    async backupData() {
        try {
            const backup = {
                timestamp: new Date().toISOString(),
                sales: await this.getSales(),
                inventory: await this.getInventory(),
                recipes: await this.getRecipes(),
                settings: localStorage.getItem('stockZeroSettings') || '{}'
            };
            const backupJson = JSON.stringify(backup, null, 2);
            const backupId = `backup_${Date.now()}`;
            localStorage.setItem(`stockzero_backup_${backupId}`, backupJson);
            return { success: true, data: backupId };
        }
        catch (error) {
            return { success: false, error: error.message };
        }
    }
    async restoreData(backupId) {
        try {
            const backupJson = localStorage.getItem(`stockzero_backup_${backupId}`);
            if (!backupJson) {
                return { success: false, error: 'Backup not found' };
            }
            const backup = JSON.parse(backupJson);
            if (backup.sales?.data) {
                for (const sale of backup.sales.data) {
                    await this.addSale(sale);
                }
            }
            if (backup.inventory?.data) {
                for (const item of backup.inventory.data) {
                    await this.addInventory(item);
                }
            }
            if (backup.recipes?.data) {
                for (const recipe of backup.recipes.data) {
                    await this.addRecipe(recipe);
                }
            }
            if (backup.settings) {
                localStorage.setItem('stockZeroSettings', backup.settings);
            }
            return { success: true };
        }
        catch (error) {
            return { success: false, error: error.message };
        }
    }
}
const databaseManager = new DatabaseManager();
export { DatabaseManager, databaseManager };
window.databaseManager = databaseManager;
window.db = databaseManager;
document.addEventListener('DOMContentLoaded', () => {
    databaseManager.initialize().then(() => {
        console.log('✅ Database manager initialized');
    }).catch((error) => {
        console.error('❌ Failed to initialize database manager:', error);
    });
});
//# sourceMappingURL=database.js.map