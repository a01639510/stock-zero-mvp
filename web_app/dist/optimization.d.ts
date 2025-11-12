import { InventoryItem } from './types';
interface OptimizationResult {
    item: InventoryItem;
    recommendedOrder: {
        quantity: number;
        cost: number;
        supplier: string;
        urgency: 'low' | 'medium' | 'high' | 'critical';
    };
    savings: {
        bulkDiscount: number;
        shipping: number;
        total: number;
    };
    confidence: number;
}
interface OrderSuggestion {
    items: Array<{
        inventoryItem: InventoryItem;
        suggestedQuantity: number;
        currentCost: number;
        optimizedCost: number;
        savings: number;
        urgency: 'low' | 'medium' | 'high' | 'critical';
    }>;
    totalCost: number;
    totalSavings: number;
    suppliers: string[];
    estimatedDelivery: Date;
}
interface InventoryOptimization {
    totalItems: number;
    optimizedItems: number;
    potentialSavings: number;
    recommendations: OptimizationResult[];
    stockoutRisk: number;
    overstockRisk: number;
}
declare class OptimizationManager {
    private readonly LOW_STOCK_THRESHOLD;
    private readonly CRITICAL_STOCK_THRESHOLD;
    private readonly BULK_DISCOUNT_THRESHOLD;
    private readonly BULK_DISCOUNT_RATE;
    private readonly OPTIMIZATION_CONFIDENCE_THRESHOLD;
    constructor();
    private initializeEventListeners;
    optimizeInventory(): Promise<InventoryOptimization>;
    private optimizeItem;
    private calculateDemandForecast;
    private calculateRecommendedOrderQuantity;
    private calculateOptimizedCost;
    private calculateShippingSavings;
    private calculateOptimizationConfidence;
    generateOrderSuggestions(): Promise<OrderSuggestion>;
    checkStockAlerts(): Promise<Array<{
        type: 'low_stock' | 'overstock' | 'expiring';
        item: InventoryItem;
        message: string;
        priority: 'low' | 'medium' | 'high' | 'critical';
    }>>;
    private groupSalesByDate;
    private runInventoryOptimization;
    private updateOptimizationUI;
    private displayStockAlerts;
    loadOptimizationData(): Promise<void>;
    loadOrderSuggestions(): Promise<void>;
}
declare const optimizationManager: OptimizationManager;
export { OptimizationManager, optimizationManager };
declare global {
    interface Window {
        optimizationManager: OptimizationManager;
        loadOptimizationData: typeof optimizationManager.loadOptimizationData;
        loadOrderSuggestions: typeof optimizationManager.loadOrderSuggestions;
    }
}
//# sourceMappingURL=optimization.d.ts.map