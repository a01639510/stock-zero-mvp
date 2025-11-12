import { SaleItem, InventoryItem, Recipe, ApiResponse } from './types';
declare class DatabaseManager {
    private supabaseUrl;
    private supabaseKey;
    private supabase;
    private isConnected;
    private connectionPromise;
    constructor();
    initialize(): Promise<void>;
    private _connect;
    private _loadConfig;
    saveConfig(url: string, key: string): Promise<void>;
    query(table: string, options?: any): Promise<ApiResponse<any[]>>;
    insert(table: string, record: any): Promise<ApiResponse<any>>;
    update(table: string, id: string, updates: any): Promise<ApiResponse<any>>;
    delete(table: string, id: string): Promise<ApiResponse<void>>;
    getSales(options?: any): Promise<ApiResponse<SaleItem[]>>;
    addSale(sale: Omit<SaleItem, 'id'>): Promise<ApiResponse<SaleItem>>;
    updateSale(id: string, updates: Partial<SaleItem>): Promise<ApiResponse<SaleItem>>;
    deleteSale(id: string): Promise<ApiResponse<void>>;
    getInventory(options?: any): Promise<ApiResponse<InventoryItem[]>>;
    addInventory(item: Omit<InventoryItem, 'id' | 'lastUpdated'>): Promise<ApiResponse<InventoryItem>>;
    updateInventory(id: string, updates: Partial<InventoryItem>): Promise<ApiResponse<InventoryItem>>;
    deleteInventory(id: string): Promise<ApiResponse<void>>;
    getRecipes(options?: any): Promise<ApiResponse<Recipe[]>>;
    addRecipe(recipe: Omit<Recipe, 'id'>): Promise<ApiResponse<Recipe>>;
    updateRecipe(id: string, updates: Partial<Recipe>): Promise<ApiResponse<Recipe>>;
    deleteRecipe(id: string): Promise<ApiResponse<void>>;
    private generateId;
    isReady(): boolean;
    getConnectionStatus(): string;
    backupData(): Promise<ApiResponse<string>>;
    restoreData(backupId: string): Promise<ApiResponse<void>>;
}
declare const databaseManager: DatabaseManager;
export { DatabaseManager, databaseManager };
declare global {
    interface Window {
        databaseManager: DatabaseManager;
        db: DatabaseManager;
    }
}
//# sourceMappingURL=database.d.ts.map