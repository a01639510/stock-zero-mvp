import { dataManager } from './data-management';
class OptimizationManager {
    constructor() {
        this.LOW_STOCK_THRESHOLD = 0.3;
        this.CRITICAL_STOCK_THRESHOLD = 0.1;
        this.BULK_DISCOUNT_THRESHOLD = 100;
        this.BULK_DISCOUNT_RATE = 0.05;
        this.OPTIMIZATION_CONFIDENCE_THRESHOLD = 0.7;
        this.initializeEventListeners();
    }
    initializeEventListeners() {
        document.addEventListener('inventoryUpdated', () => this.runInventoryOptimization());
    }
    async optimizeInventory() {
        try {
            const [inventory, sales] = await Promise.all([
                dataManager.loadInventory(),
                dataManager.loadSales()
            ]);
            const recommendations = [];
            let totalPotentialSavings = 0;
            let optimizedItems = 0;
            let stockoutRisk = 0;
            let overstockRisk = 0;
            for (const item of inventory) {
                const optimization = await this.optimizeItem(item, sales);
                if (optimization && optimization.confidence >= this.OPTIMIZATION_CONFIDENCE_THRESHOLD) {
                    recommendations.push(optimization);
                    totalPotentialSavings += optimization.savings.total;
                    optimizedItems++;
                }
                const stockRatio = item.quantity / item.maxQuantity;
                if (stockRatio <= this.CRITICAL_STOCK_THRESHOLD) {
                    stockoutRisk++;
                }
                else if (stockRatio >= 0.9) {
                    overstockRisk++;
                }
            }
            recommendations.sort((a, b) => {
                const urgencyOrder = { critical: 4, high: 3, medium: 2, low: 1 };
                const urgencyDiff = urgencyOrder[b.recommendedOrder.urgency] - urgencyOrder[a.recommendedOrder.urgency];
                if (urgencyDiff !== 0)
                    return urgencyDiff;
                return b.savings.total - a.savings.total;
            });
            return {
                totalItems: inventory.length,
                optimizedItems,
                potentialSavings: totalPotentialSavings,
                recommendations,
                stockoutRisk: stockoutRisk / inventory.length,
                overstockRisk: overstockRisk / inventory.length
            };
        }
        catch (error) {
            console.error('Error optimizing inventory:', error);
            return {
                totalItems: 0,
                optimizedItems: 0,
                potentialSavings: 0,
                recommendations: [],
                stockoutRisk: 0,
                overstockRisk: 0
            };
        }
    }
    async optimizeItem(item, sales) {
        try {
            const stockRatio = item.quantity / item.maxQuantity;
            let urgency = 'low';
            if (stockRatio <= this.CRITICAL_STOCK_THRESHOLD) {
                urgency = 'critical';
            }
            else if (stockRatio <= this.LOW_STOCK_THRESHOLD) {
                urgency = 'high';
            }
            else if (stockRatio <= 0.5) {
                urgency = 'medium';
            }
            const demandForecast = await this.calculateDemandForecast(item, sales);
            const recommendedQuantity = this.calculateRecommendedOrderQuantity(item, demandForecast);
            if (recommendedQuantity <= 0) {
                return null;
            }
            const currentCost = recommendedQuantity * item.cost;
            const optimizedCost = this.calculateOptimizedCost(item, recommendedQuantity);
            const bulkDiscount = Math.max(0, currentCost - optimizedCost);
            const shippingSavings = this.calculateShippingSavings(item, recommendedQuantity);
            const totalSavings = bulkDiscount + shippingSavings;
            const confidence = this.calculateOptimizationConfidence(item, sales, demandForecast);
            return {
                item,
                recommendedOrder: {
                    quantity: recommendedQuantity,
                    cost: optimizedCost,
                    supplier: item.supplier || 'Proveedor principal',
                    urgency
                },
                savings: {
                    bulkDiscount,
                    shipping: shippingSavings,
                    total: totalSavings
                },
                confidence
            };
        }
        catch (error) {
            console.error(`Error optimizing item ${item.name}:`, error);
            return null;
        }
    }
    async calculateDemandForecast(item, sales) {
        try {
            const itemSales = sales.filter(sale => sale.productName.toLowerCase().includes(item.name.toLowerCase()));
            if (itemSales.length === 0) {
                return item.minQuantity;
            }
            const salesByDate = this.groupSalesByDate(itemSales);
            const dailySales = Object.values(salesByDate).map(day => day.quantity);
            const avgDailySales = dailySales.reduce((sum, qty) => sum + qty, 0) / dailySales.length;
            const leadTimeDays = 7;
            const leadTimeDemand = avgDailySales * leadTimeDays;
            const safetyStock = leadTimeDemand * 0.2;
            return leadTimeDemand + safetyStock;
        }
        catch (error) {
            console.error(`Error calculating demand forecast for ${item.name}:`, error);
            return item.minQuantity;
        }
    }
    calculateRecommendedOrderQuantity(item, demandForecast) {
        const currentStock = item.quantity;
        const maxStock = item.maxQuantity;
        const optimalQuantity = Math.ceil(demandForecast - currentStock + item.minQuantity);
        const maxOrderQuantity = maxStock - currentStock;
        return Math.max(0, Math.min(optimalQuantity, maxOrderQuantity));
    }
    calculateOptimizedCost(item, quantity) {
        let cost = quantity * item.cost;
        if (quantity >= this.BULK_DISCOUNT_THRESHOLD) {
            cost *= (1 - this.BULK_DISCOUNT_RATE);
        }
        return cost;
    }
    calculateShippingSavings(_item, quantity) {
        const baseShipping = 10;
        const bulkShipping = quantity >= this.BULK_DISCOUNT_THRESHOLD ? baseShipping * 0.5 : baseShipping;
        return baseShipping - bulkShipping;
    }
    calculateOptimizationConfidence(item, sales, demandForecast) {
        let confidence = 0.5;
        const itemSales = sales.filter(sale => sale.productName.toLowerCase().includes(item.name.toLowerCase()));
        if (itemSales.length > 10) {
            confidence += 0.2;
        }
        else if (itemSales.length > 5) {
            confidence += 0.1;
        }
        if (demandForecast > 0 && demandForecast <= item.maxQuantity * 0.8) {
            confidence += 0.2;
        }
        const stockRatio = item.quantity / item.maxQuantity;
        if (stockRatio <= this.CRITICAL_STOCK_THRESHOLD || stockRatio >= 0.95) {
            confidence -= 0.1;
        }
        return Math.max(0, Math.min(1, confidence));
    }
    async generateOrderSuggestions() {
        try {
            const optimization = await this.optimizeInventory();
            const criticalItems = optimization.recommendations
                .filter(rec => rec.recommendedOrder.urgency === 'critical' || rec.recommendedOrder.urgency === 'high')
                .slice(0, 10);
            const suggestions = criticalItems.map(rec => ({
                inventoryItem: rec.item,
                suggestedQuantity: rec.recommendedOrder.quantity,
                currentCost: rec.recommendedOrder.quantity * rec.item.cost,
                optimizedCost: rec.recommendedOrder.cost,
                savings: rec.savings.total,
                urgency: rec.recommendedOrder.urgency
            }));
            const totalCost = suggestions.reduce((sum, sug) => sum + sug.optimizedCost, 0);
            const totalSavings = suggestions.reduce((sum, sug) => sum + sug.savings, 0);
            const suppliers = [...new Set(suggestions.map(sug => sug.inventoryItem.supplier || 'Proveedor principal'))];
            const avgUrgency = suggestions.reduce((sum, sug) => {
                const urgencyDays = { critical: 2, high: 3, medium: 4, low: 5 };
                return sum + urgencyDays[sug.urgency];
            }, 0) / suggestions.length;
            const estimatedDelivery = new Date();
            estimatedDelivery.setDate(estimatedDelivery.getDate() + Math.ceil(avgUrgency));
            return {
                items: suggestions,
                totalCost,
                totalSavings,
                suppliers,
                estimatedDelivery
            };
        }
        catch (error) {
            console.error('Error generating order suggestions:', error);
            return {
                items: [],
                totalCost: 0,
                totalSavings: 0,
                suppliers: [],
                estimatedDelivery: new Date()
            };
        }
    }
    async checkStockAlerts() {
        try {
            const inventory = await dataManager.loadInventory();
            const alerts = [];
            for (const item of inventory) {
                const stockRatio = item.quantity / item.maxQuantity;
                if (stockRatio <= this.CRITICAL_STOCK_THRESHOLD) {
                    alerts.push({
                        type: 'low_stock',
                        item,
                        message: `Stock crítico: ${item.name} (${item.quantity} ${item.unit})`,
                        priority: 'critical'
                    });
                }
                else if (stockRatio <= this.LOW_STOCK_THRESHOLD) {
                    alerts.push({
                        type: 'low_stock',
                        item,
                        message: `Bajo stock: ${item.name} (${item.quantity} ${item.unit})`,
                        priority: 'high'
                    });
                }
                if (stockRatio >= 0.9) {
                    alerts.push({
                        type: 'overstock',
                        item,
                        message: `Sobrestock: ${item.name} (${item.quantity} ${item.unit}, max: ${item.maxQuantity})`,
                        priority: 'medium'
                    });
                }
            }
            const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
            alerts.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);
            return alerts;
        }
        catch (error) {
            console.error('Error checking stock alerts:', error);
            return [];
        }
    }
    groupSalesByDate(sales) {
        const grouped = {};
        sales.forEach(sale => {
            const dateKey = new Date(sale.date).toISOString().split('T')[0];
            if (!grouped[dateKey]) {
                grouped[dateKey] = { quantity: 0, revenue: 0 };
            }
            grouped[dateKey].quantity += sale.quantity;
            grouped[dateKey].revenue += sale.total;
        });
        return grouped;
    }
    async runInventoryOptimization() {
        try {
            const optimization = await this.optimizeInventory();
            this.updateOptimizationUI(optimization);
            const alerts = await this.checkStockAlerts();
            if (alerts.length > 0) {
                this.displayStockAlerts(alerts);
            }
        }
        catch (error) {
            console.error('Error running inventory optimization:', error);
        }
    }
    updateOptimizationUI(optimization) {
        const optimizationElement = document.getElementById('optimizationSummary');
        if (optimizationElement) {
            optimizationElement.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-white p-4 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Items Optimizados</h3>
                        <p class="text-2xl font-bold text-blue-600">${optimization.optimizedItems}</p>
                    </div>
                    <div class="bg-white p-4 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Ahorro Potencial</h3>
                        <p class="text-2xl font-bold text-green-600">$${optimization.potentialSavings.toLocaleString()}</p>
                    </div>
                    <div class="bg-white p-4 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Riesgo de Agotamiento</h3>
                        <p class="text-2xl font-bold text-red-600">${(optimization.stockoutRisk * 100).toFixed(1)}%</p>
                    </div>
                    <div class="bg-white p-4 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Riesgo de Sobrestock</h3>
                        <p class="text-2xl font-bold text-orange-600">${(optimization.overstockRisk * 100).toFixed(1)}%</p>
                    </div>
                </div>
            `;
        }
        const recommendationsElement = document.getElementById('optimizationRecommendations');
        if (recommendationsElement) {
            const topRecommendations = optimization.recommendations.slice(0, 5);
            recommendationsElement.innerHTML = `
                <div class="space-y-4">
                    ${topRecommendations.map(rec => `
                        <div class="bg-white p-4 rounded-lg shadow border-l-4 ${rec.recommendedOrder.urgency === 'critical' ? 'border-red-500' :
                rec.recommendedOrder.urgency === 'high' ? 'border-orange-500' :
                    rec.recommendedOrder.urgency === 'medium' ? 'border-yellow-500' :
                        'border-green-500'}">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="font-semibold text-gray-800">${rec.item.name}</h4>
                                    <p class="text-sm text-gray-600">
                                        Ordenar ${rec.recommendedOrder.quantity} ${rec.item.unit} - 
                                        $${rec.recommendedOrder.cost.toLocaleString()}
                                    </p>
                                    <p class="text-sm text-green-600">
                                        Ahorro: $${rec.savings.total.toLocaleString()}
                                    </p>
                                </div>
                                <span class="px-2 py-1 text-xs rounded-full ${rec.recommendedOrder.urgency === 'critical' ? 'bg-red-100 text-red-800' :
                rec.recommendedOrder.urgency === 'high' ? 'bg-orange-100 text-orange-800' :
                    rec.recommendedOrder.urgency === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'}">
                                    ${rec.recommendedOrder.urgency.toUpperCase()}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }
    displayStockAlerts(alerts) {
        console.log('Stock alerts:', alerts);
        alerts.forEach(alert => {
            if (alert.priority === 'critical' || alert.priority === 'high') {
                if (window.showError) {
                    window.showError(alert.message);
                }
            }
        });
    }
    async loadOptimizationData() {
        await this.runInventoryOptimization();
    }
    async loadOrderSuggestions() {
        try {
            const suggestions = await this.generateOrderSuggestions();
            const suggestionsElement = document.getElementById('orderSuggestions');
            if (suggestionsElement) {
                suggestionsElement.innerHTML = `
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold text-gray-800 mb-4">Sugerencias de Pedido</h3>
                        <div class="space-y-4">
                            ${suggestions.items.map(suggestion => `
                                <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                                    <div>
                                        <span class="font-medium">${suggestion.inventoryItem.name}</span>
                                        <span class="text-sm text-gray-600 ml-2">
                                            ${suggestion.suggestedQuantity} ${suggestion.inventoryItem.unit}
                                        </span>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-sm text-gray-600">$${suggestion.optimizedCost.toLocaleString()}</div>
                                        <div class="text-xs text-green-600">Ahorro: $${suggestion.savings.toLocaleString()}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="mt-4 pt-4 border-t">
                            <div class="flex justify-between items-center">
                                <span class="font-semibold">Total:</span>
                                <span class="font-bold">$${suggestions.totalCost.toLocaleString()}</span>
                            </div>
                            <div class="flex justify-between items-center text-green-600">
                                <span>Ahorro total:</span>
                                <span class="font-bold">$${suggestions.totalSavings.toLocaleString()}</span>
                            </div>
                            <div class="text-sm text-gray-600 mt-2">
                                Proveedores: ${suggestions.suppliers.join(', ')}
                            </div>
                            <div class="text-sm text-gray-600">
                                Entrega estimada: ${suggestions.estimatedDelivery.toLocaleDateString()}
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        catch (error) {
            console.error('Error loading order suggestions:', error);
        }
    }
}
const optimizationManager = new OptimizationManager();
export { OptimizationManager, optimizationManager };
window.optimizationManager = optimizationManager;
window.loadOptimizationData = () => optimizationManager.loadOptimizationData();
window.loadOrderSuggestions = () => optimizationManager.loadOrderSuggestions();
//# sourceMappingURL=optimization.js.map