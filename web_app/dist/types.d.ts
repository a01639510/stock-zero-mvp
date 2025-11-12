export interface User {
    id: string;
    email: string;
    name: string;
    role: string;
    createdAt: Date;
}
export interface Session {
    user: User;
    token: string;
    expiresAt: number;
}
export interface SaleItem {
    id: string;
    productName: string;
    quantity: number;
    price: number;
    total: number;
    date: Date;
    category?: string;
}
export interface InventoryItem {
    id: string;
    name: string;
    quantity: number;
    minQuantity: number;
    maxQuantity: number;
    unit: string;
    category: string;
    cost: number;
    supplier?: string;
    lastUpdated: Date;
}
export interface Recipe {
    id: string;
    name: string;
    ingredients: RecipeIngredient[];
    instructions: string[];
    yield: number;
    category: string;
    costPerUnit: number;
    sellingPrice: number;
    profitMargin: number;
}
export interface RecipeIngredient {
    id: string;
    name: string;
    quantity: number;
    unit: string;
    cost: number;
}
export interface Settings {
    theme: 'light' | 'dark';
    currency: string;
    language: string;
    notifications: boolean;
    autoBackup: boolean;
    backupInterval: number;
}
export interface KPIs {
    totalSales: number;
    totalInventory: number;
    lowStockItems: number;
    totalRecipes: number;
    profitMargin: number;
    inventoryValue: number;
    salesTrend: number[];
    topProducts: SaleItem[];
}
export interface AppState {
    user: User | null;
    isAuthenticated: boolean;
    currentTab: string;
    data: {
        sales: SaleItem[];
        inventory: InventoryItem[];
        recipes: Recipe[];
        settings: Settings;
    };
    kpis: Partial<KPIs>;
    loading: boolean;
    error: string | null;
}
export interface DatabaseConfig {
    supabaseUrl: string;
    supabaseKey: string;
}
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
}
export interface ChartData {
    x: string[];
    y: number[];
    type: string;
    name: string;
}
export interface PlotlyData {
    data: any[];
    layout: any;
    config?: any;
}
declare global {
    interface Window {
        Plotly: any;
        Papa: any;
        supabase: any;
        loadDashboardKPIs: () => void | Promise<void>;
        loadInventoryList: () => void | Promise<void>;
        loadSalesList: () => void | Promise<void>;
        loadRecipesList: () => void | Promise<void>;
        loadAnalyticsCharts: () => void | Promise<void>;
    }
}
export interface SupabaseClient {
    from(table: string): any;
    auth: any;
}
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';
export type TabType = 'dashboard' | 'inventory' | 'sales' | 'recipes' | 'analytics' | 'settings';
export type ChartType = 'line' | 'bar' | 'pie' | 'scatter' | 'histogram';
export interface LoginForm {
    email: string;
    password: string;
}
export interface InventoryForm {
    name: string;
    quantity: number;
    minQuantity: number;
    maxQuantity: number;
    unit: string;
    category: string;
    cost: number;
    supplier?: string;
}
export interface SaleForm {
    productName: string;
    quantity: number;
    price: number;
    category?: string;
}
export interface ValidationError {
    field: string;
    message: string;
}
export interface ValidationResult {
    isValid: boolean;
    errors: ValidationError[];
}
//# sourceMappingURL=types.d.ts.map