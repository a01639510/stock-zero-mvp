import { SaleItem, InventoryItem, Recipe, ApiResponse, Settings } from './types';
declare class DataManager {
    private cache;
    private cacheTimeout;
    private subscribers;
    constructor();
    private initializeEventListeners;
    private setCache;
    private getCache;
    private clearCache;
    subscribe(event: string, callback: Function): void;
    unsubscribe(event: string, callback: Function): void;
    private notifySubscribers;
    loadSales(): Promise<SaleItem[]>;
    addSale(saleData: Omit<SaleItem, 'id' | 'date' | 'total'>): Promise<ApiResponse<SaleItem>>;
    updateSale(id: string, updates: Partial<SaleItem>): Promise<ApiResponse<SaleItem>>;
    deleteSale(id: string): Promise<ApiResponse<void>>;
    loadInventory(): Promise<InventoryItem[]>;
    addInventory(item: Omit<InventoryItem, 'id' | 'lastUpdated'>): Promise<ApiResponse<InventoryItem>>;
    updateInventory(id: string, updates: Partial<InventoryItem>): Promise<ApiResponse<InventoryItem>>;
    deleteInventory(id: string): Promise<ApiResponse<void>>;
    private updateInventoryFromSale;
    loadRecipes(): Promise<Recipe[]>;
    addRecipe(recipe: Omit<Recipe, 'id'>): Promise<ApiResponse<Recipe>>;
    updateRecipe(id: string, updates: Partial<Recipe>): Promise<ApiResponse<Recipe>>;
    deleteRecipe(id: string): Promise<ApiResponse<void>>;
    loadSettings(): Promise<Settings>;
    saveSettings(settings: Settings): Promise<ApiResponse<Settings>>;
    getSalesReport(startDate: Date, endDate: Date): Promise<{
        totalSales: number;
        totalRevenue: number;
        averageOrderValue: number;
        topProducts: SaleItem[];
        dailySales: {
            date: string;
            sales: number;
            revenue: number;
        }[];
    }>;
    getInventoryReport(): Promise<{
        totalItems: number;
        lowStockItems: number;
        totalValue: number;
        itemsByCategory: {
            category: string;
            count: number;
            value: number;
        }[];
    }>;
    validateSaleData(data: any): {
        isValid: boolean;
        errors: string[];
    };
    validateInventoryData(data: any): {
        isValid: boolean;
        errors: string[];
    };
    exportData(type: 'sales' | 'inventory' | 'recipes'): Promise<string>;
    private convertToCSV;
}
declare const dataManager: DataManager;
export { DataManager, dataManager };
declare global {
    interface Window {
        dataManager: DataManager;
    }
}
//# sourceMappingURL=data-management.d.ts.map