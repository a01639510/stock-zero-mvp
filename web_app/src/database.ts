// Stock Zero - Database Integration TypeScript

import { DatabaseConfig, SaleItem, InventoryItem, Recipe, ApiResponse } from './types';

class DatabaseManager {
    private supabaseUrl: string | null = null;
    private supabaseKey: string | null = null;
    private supabase: any = null;
    private isConnected: boolean = false;
    private connectionPromise: Promise<void> | null = null;

    constructor() {
        // Constructor logic moved to initialize method
    }

    async initialize(): Promise<void> {
        if (this.connectionPromise) return this.connectionPromise;
        this.connectionPromise = this._connect();
        return this.connectionPromise;
    }

    private async _connect(): Promise<void> {
        try {
            const config = await this._loadConfig();

            if (config.supabaseUrl && config.supabaseKey) {
                this.supabaseUrl = config.supabaseUrl;
                this.supabaseKey = config.supabaseKey;
                
                // Simulate successful connection to avoid infinite loading
                console.log("✅ Database configuration found");
                this.isConnected = true;
                
                // Initialize Supabase client if available
                if (typeof window !== 'undefined' && window.supabase) {
                    this.supabase = window.supabase.createClient(
                        this.supabaseUrl,
                        this.supabaseKey
                    );
                    console.log("✅ Supabase client initialized");
                }
                
            } else {
                console.warn("⚠️ No database configuration found, using local storage");
                this.isConnected = true; // Allow app to work with local storage
            }
        } catch (error) {
            console.error("❌ Database connection error:", error);
            this.isConnected = false;
            throw error;
        }
    }

    private async _loadConfig(): Promise<DatabaseConfig> {
        return new Promise((resolve) => {
            // Try to load from environment first
            const supabaseUrl = process.env.SUPABASE_URL || 
                              (document.querySelector('meta[name="supabase-url"]') as HTMLMetaElement)?.content ||
                              localStorage.getItem('supabase_url');
            
            const supabaseKey = process.env.SUPABASE_KEY || 
                              (document.querySelector('meta[name="supabase-key"]') as HTMLMetaElement)?.content ||
                              localStorage.getItem('supabase_key');

            resolve({
                supabaseUrl: supabaseUrl || '',
                supabaseKey: supabaseKey || ''
            });
        });
    }

    async saveConfig(url: string, key: string): Promise<void> {
        localStorage.setItem('supabase_url', url);
        localStorage.setItem('supabase_key', key);
        
        this.supabaseUrl = url;
        this.supabaseKey = key;
        
        // Reinitialize connection
        this.connectionPromise = null;
        await this.initialize();
    }

    // Generic query method
    async query(table: string, options: any = {}): Promise<ApiResponse<any[]>> {
        try {
            if (!this.isConnected) {
                await this.initialize();
            }

            if (this.supabase) {
                let query = this.supabase.from(table).select();
                
                if (options.filters) {
                    options.filters.forEach((filter: any) => {
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
            } else {
                // Fallback to local storage
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                return { success: true, data };
            }
        } catch (error) {
            console.error(`Exception in query for table ${table}:`, error);
            return { success: false, error: (error as Error).message };
        }
    }

    // Generic insert method
    async insert(table: string, record: any): Promise<ApiResponse<any>> {
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
            } else {
                // Fallback to local storage
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                
                const newRecord = { ...record, id: this.generateId() };
                data.push(newRecord);
                
                localStorage.setItem(`stockzero_${table}`, JSON.stringify(data));
                return { success: true, data: newRecord };
            }
        } catch (error) {
            console.error(`Exception in insert for table ${table}:`, error);
            return { success: false, error: (error as Error).message };
        }
    }

    // Generic update method
    async update(table: string, id: string, updates: any): Promise<ApiResponse<any>> {
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
            } else {
                // Fallback to local storage
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                
                const index = data.findIndex((item: any) => item.id === id);
                if (index !== -1) {
                    data[index] = { ...data[index], ...updates };
                    localStorage.setItem(`stockzero_${table}`, JSON.stringify(data));
                    return { success: true, data: data[index] };
                }
                
                return { success: false, error: 'Record not found' };
            }
        } catch (error) {
            console.error(`Exception in update for table ${table}:`, error);
            return { success: false, error: (error as Error).message };
        }
    }

    // Generic delete method
    async delete(table: string, id: string): Promise<ApiResponse<void>> {
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
            } else {
                // Fallback to local storage
                const localData = localStorage.getItem(`stockzero_${table}`);
                const data = localData ? JSON.parse(localData) : [];
                
                const filteredData = data.filter((item: any) => item.id !== id);
                localStorage.setItem(`stockzero_${table}`, JSON.stringify(filteredData));
                
                return { success: true };
            }
        } catch (error) {
            console.error(`Exception in delete for table ${table}:`, error);
            return { success: false, error: (error as Error).message };
        }
    }

    // Specific methods for different data types
    async getSales(options: any = {}): Promise<ApiResponse<SaleItem[]>> {
        return this.query('sales', options);
    }

    async addSale(sale: Omit<SaleItem, 'id'>): Promise<ApiResponse<SaleItem>> {
        return this.insert('sales', sale);
    }

    async updateSale(id: string, updates: Partial<SaleItem>): Promise<ApiResponse<SaleItem>> {
        return this.update('sales', id, updates);
    }

    async deleteSale(id: string): Promise<ApiResponse<void>> {
        return this.delete('sales', id);
    }

    async getInventory(options: any = {}): Promise<ApiResponse<InventoryItem[]>> {
        return this.query('inventory', options);
    }

    async addInventory(item: Omit<InventoryItem, 'id' | 'lastUpdated'>): Promise<ApiResponse<InventoryItem>> {
        const inventoryItem = {
            ...item,
            lastUpdated: new Date()
        };
        return this.insert('inventory', inventoryItem);
    }

    async updateInventory(id: string, updates: Partial<InventoryItem>): Promise<ApiResponse<InventoryItem>> {
        return this.update('inventory', id, { ...updates, lastUpdated: new Date() });
    }

    async deleteInventory(id: string): Promise<ApiResponse<void>> {
        return this.delete('inventory', id);
    }

    async getRecipes(options: any = {}): Promise<ApiResponse<Recipe[]>> {
        return this.query('recipes', options);
    }

    async addRecipe(recipe: Omit<Recipe, 'id'>): Promise<ApiResponse<Recipe>> {
        return this.insert('recipes', recipe);
    }

    async updateRecipe(id: string, updates: Partial<Recipe>): Promise<ApiResponse<Recipe>> {
        return this.update('recipes', id, updates);
    }

    async deleteRecipe(id: string): Promise<ApiResponse<void>> {
        return this.delete('recipes', id);
    }

    // Utility methods
    private generateId(): string {
        return Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }

    isReady(): boolean {
        return this.isConnected;
    }

    getConnectionStatus(): string {
        if (this.supabase) return 'supabase';
        if (this.isConnected) return 'local';
        return 'disconnected';
    }

    // Backup and restore methods
    async backupData(): Promise<ApiResponse<string>> {
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
        } catch (error) {
            return { success: false, error: (error as Error).message };
        }
    }

    async restoreData(backupId: string): Promise<ApiResponse<void>> {
        try {
            const backupJson = localStorage.getItem(`stockzero_backup_${backupId}`);
            if (!backupJson) {
                return { success: false, error: 'Backup not found' };
            }
            
            const backup = JSON.parse(backupJson);
            
            // Restore each data type
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
        } catch (error) {
            return { success: false, error: (error as Error).message };
        }
    }
}

// Create singleton instance
const databaseManager = new DatabaseManager();

// Export for use in other modules
export { DatabaseManager, databaseManager };

// Make available globally
declare global {
    interface Window {
        databaseManager: DatabaseManager;
        db: DatabaseManager;
    }
}

window.databaseManager = databaseManager;
window.db = databaseManager;

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    databaseManager.initialize().then(() => {
        console.log('✅ Database manager initialized');
    }).catch((error) => {
        console.error('❌ Failed to initialize database manager:', error);
    });
});