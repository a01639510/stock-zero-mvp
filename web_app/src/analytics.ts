// Stock Zero - Analytics Module TypeScript

import { SaleItem, InventoryItem, Recipe, PlotlyData } from './types';
import { dataManager } from './data-management';

class AnalyticsManager {
    private charts: Map<string, any> = new Map();
    private colors = {
        primary: '#2563eb',
        secondary: '#7c3aed',
        success: '#059669',
        warning: '#d97706',
        danger: '#dc2626',
        info: '#0891b2'
    };

    constructor() {
        this.initializeEventListeners();
    }

    private initializeEventListeners(): void {
        document.addEventListener('salesUpdated', () => this.refreshSalesAnalytics());
        document.addEventListener('inventoryUpdated', () => this.refreshInventoryAnalytics());
        document.addEventListener('recipesUpdated', () => this.refreshRecipeAnalytics());
    }

    // Dashboard KPIs
    async loadDashboardKPIs(): Promise<void> {
        try {
            const [sales, inventory, recipes] = await Promise.all([
                dataManager.loadSales(),
                dataManager.loadInventory(),
                dataManager.loadRecipes()
            ]);

            this.updateKPICards(sales, inventory, recipes);
            this.loadDashboardCharts(sales, inventory);
        } catch (error) {
            console.error('Error loading dashboard KPIs:', error);
        }
    }

    private updateKPICards(sales: SaleItem[], inventory: InventoryItem[], recipes: Recipe[]): void {
        const totalSales = sales.length;
        const totalRevenue = sales.reduce((sum, sale) => sum + sale.total, 0);
        const lowStockItems = inventory.filter(item => item.quantity <= item.minQuantity).length;
        const totalRecipes = recipes.length;
        const inventoryValue = inventory.reduce((sum, item) => sum + (item.quantity * item.cost), 0);
        const averageProfitMargin = recipes.length > 0 
            ? recipes.reduce((sum, recipe) => sum + recipe.profitMargin, 0) / recipes.length 
            : 0;

        this.updateKPICard('totalSales', totalSales.toLocaleString(), 'Total Ventas');
        this.updateKPICard('totalRevenue', `$${totalRevenue.toLocaleString()}`, 'Ingresos Totales');
        this.updateKPICard('lowStockItems', lowStockItems.toString(), 'Productos con Bajo Stock');
        this.updateKPICard('totalRecipes', totalRecipes.toString(), 'Recetas Activas');
        this.updateKPICard('inventoryValue', `$${inventoryValue.toLocaleString()}`, 'Valor de Inventario');
        this.updateKPICard('profitMargin', `${averageProfitMargin.toFixed(1)}%`, 'Margen de Ganancia Promedio');
    }

    private updateKPICard(elementId: string, value: string, label: string): void {
        const element = document.getElementById(elementId);
        if (element) {
            const valueElement = element.querySelector('.kpi-value');
            const labelElement = element.querySelector('.kpi-label');
            
            if (valueElement) valueElement.textContent = value;
            if (labelElement) labelElement.textContent = label;
        }
    }

    private async loadDashboardCharts(sales: SaleItem[], inventory: InventoryItem[]): Promise<void> {
        try {
            // Sales trend chart
            await this.createSalesTrendChart(sales, 'salesTrendChart');
            
            // Inventory status chart
            await this.createInventoryStatusChart(inventory, 'inventoryStatusChart');
            
            // Top products chart
            await this.createTopProductsChart(sales, 'topProductsChart');
        } catch (error) {
            console.error('Error loading dashboard charts:', error);
        }
    }

    // Sales analytics
    async loadSalesAnalytics(): Promise<void> {
        try {
            const sales = await dataManager.loadSales();
            await this.createSalesTrendChart(sales, 'salesAnalyticsChart');
            await this.createSalesByCategoryChart(sales, 'salesCategoryChart');
        } catch (error) {
            console.error('Error loading sales analytics:', error);
        }
    }

    private async createSalesTrendChart(sales: SaleItem[], containerId: string): Promise<void> {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Group sales by date
        const salesByDate = this.groupSalesByDate(sales, 'day');
        
        const chartData: PlotlyData = {
            data: [{
                x: Object.keys(salesByDate),
                y: Object.values(salesByDate).map(day => day.revenue),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Ingresos',
                line: { color: this.colors.primary, width: 3 },
                marker: { color: this.colors.primary, size: 6 }
            }],
            layout: {
                title: 'Tendencia de Ventas',
                xaxis: { title: 'Fecha' },
                yaxis: { title: 'Ingresos ($)' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#374151' },
                margin: { t: 40, r: 20, b: 40, l: 60 }
            },
            config: { responsive: true, displayModeBar: false }
        };

        this.renderChart(containerId, chartData);
    }

    private async createSalesByCategoryChart(sales: SaleItem[], containerId: string): Promise<void> {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Group sales by category
        const salesByCategory = this.groupSalesByCategory(sales);
        
        const chartData: PlotlyData = {
            data: [{
                labels: Object.keys(salesByCategory),
                values: Object.values(salesByCategory),
                type: 'pie',
                marker: {
                    colors: [this.colors.primary, this.colors.secondary, this.colors.success, this.colors.warning, this.colors.info]
                },
                textinfo: 'label+percent',
                textposition: 'outside'
            }],
            layout: {
                title: 'Ventas por Categoría',
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#374151' },
                margin: { t: 40, r: 20, b: 20, l: 20 }
            },
            config: { responsive: true, displayModeBar: false }
        };

        this.renderChart(containerId, chartData);
    }

    // Inventory analytics
    async loadInventoryAnalytics(): Promise<void> {
        try {
            const inventory = await dataManager.loadInventory();
            await this.createInventoryStatusChart(inventory, 'inventoryAnalyticsChart');
            await this.createInventoryByCategoryChart(inventory, 'inventoryCategoryChart');
        } catch (error) {
            console.error('Error loading inventory analytics:', error);
        }
    }

    private async createInventoryStatusChart(inventory: InventoryItem[], containerId: string): Promise<void> {
        const container = document.getElementById(containerId);
        if (!container) return;

        const statusData = this.categorizeInventoryStatus(inventory);
        
        const chartData: PlotlyData = {
            data: [{
                x: ['Suficiente', 'Bajo', 'Crítico'],
                y: [statusData.sufficient, statusData.low, statusData.critical],
                type: 'bar',
                marker: {
                    color: [this.colors.success, this.colors.warning, this.colors.danger]
                },
                text: [statusData.sufficient, statusData.low, statusData.critical],
                textposition: 'auto'
            }],
            layout: {
                title: 'Estado del Inventario',
                xaxis: { title: 'Estado' },
                yaxis: { title: 'Número de Productos' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#374151' },
                margin: { t: 40, r: 20, b: 40, l: 60 }
            },
            config: { responsive: true, displayModeBar: false }
        };

        this.renderChart(containerId, chartData);
    }

    private async createInventoryByCategoryChart(inventory: InventoryItem[], containerId: string): Promise<void> {
        const container = document.getElementById(containerId);
        if (!container) return;

        const inventoryByCategory = this.groupInventoryByCategory(inventory);
        
        const chartData: PlotlyData = {
            data: [{
                x: Object.keys(inventoryByCategory),
                y: Object.values(inventoryByCategory).map(cat => cat.count),
                type: 'bar',
                marker: {
                    color: this.colors.primary
                },
                text: Object.values(inventoryByCategory).map(cat => cat.count),
                textposition: 'auto'
            }],
            layout: {
                title: 'Inventario por Categoría',
                xaxis: { title: 'Categoría', tickangle: -45 },
                yaxis: { title: 'Número de Productos' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#374151' },
                margin: { t: 40, r: 20, b: 80, l: 60 }
            },
            config: { responsive: true, displayModeBar: false }
        };

        this.renderChart(containerId, chartData);
    }

    // Recipe analytics
    async loadRecipeAnalytics(): Promise<void> {
        try {
            const recipes = await dataManager.loadRecipes();
            await this.createRecipeProfitabilityChart(recipes, 'recipeProfitabilityChart');
        } catch (error) {
            console.error('Error loading recipe analytics:', error);
        }
    }

    private async createRecipeProfitabilityChart(recipes: Recipe[], containerId: string): Promise<void> {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Sort recipes by profit margin
        const sortedRecipes = [...recipes].sort((a, b) => b.profitMargin - a.profitMargin);
        
        const chartData: PlotlyData = {
            data: [{
                x: sortedRecipes.map(recipe => recipe.name),
                y: sortedRecipes.map(recipe => recipe.profitMargin),
                type: 'bar',
                marker: {
                    color: sortedRecipes.map(recipe => 
                        recipe.profitMargin > 50 ? this.colors.success :
                        recipe.profitMargin > 30 ? this.colors.warning :
                        this.colors.danger
                    )
                },
                text: sortedRecipes.map(recipe => `${recipe.profitMargin.toFixed(1)}%`),
                textposition: 'auto'
            }],
            layout: {
                title: 'Rentabilidad de Recetas',
                xaxis: { title: 'Receta', tickangle: -45 },
                yaxis: { title: 'Margen de Ganancia (%)' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#374151' },
                margin: { t: 40, r: 20, b: 80, l: 60 }
            },
            config: { responsive: true, displayModeBar: false }
        };

        this.renderChart(containerId, chartData);
    }

    // Top products chart
    private async createTopProductsChart(sales: SaleItem[], containerId: string): Promise<void> {
        const container = document.getElementById(containerId);
        if (!container) return;

        const topProducts = this.getTopProducts(sales, 5);
        
        const chartData: PlotlyData = {
            data: [{
                x: topProducts.map(product => product.name),
                y: topProducts.map(product => product.revenue),
                type: 'bar',
                marker: {
                    color: this.colors.secondary
                },
                text: topProducts.map(product => `$${product.revenue.toLocaleString()}`),
                textposition: 'auto'
            }],
            layout: {
                title: 'Top 5 Productos',
                xaxis: { title: 'Producto', tickangle: -45 },
                yaxis: { title: 'Ingresos ($)' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#374151' },
                margin: { t: 40, r: 20, b: 80, l: 60 }
            },
            config: { responsive: true, displayModeBar: false }
        };

        this.renderChart(containerId, chartData);
    }

    // Utility methods
    private groupSalesByDate(sales: SaleItem[], groupBy: 'day' | 'week' | 'month' = 'day'): Record<string, { revenue: number; count: number }> {
        const grouped: Record<string, { revenue: number; count: number }> = {};
        
        sales.forEach(sale => {
            const date = new Date(sale.date);
            let key: string;
            
            switch (groupBy) {
                case 'day':
                    key = date.toISOString().split('T')[0];
                    break;
                case 'week':
                    const weekStart = new Date(date);
                    weekStart.setDate(date.getDate() - date.getDay());
                    key = weekStart.toISOString().split('T')[0];
                    break;
                case 'month':
                    key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                    break;
            }
            
            if (!grouped[key]) {
                grouped[key] = { revenue: 0, count: 0 };
            }
            
            grouped[key].revenue += sale.total;
            grouped[key].count += 1;
        });
        
        return grouped;
    }

    private groupSalesByCategory(sales: SaleItem[]): Record<string, number> {
        const grouped: Record<string, number> = {};
        
        sales.forEach(sale => {
            const category = sale.category || 'Sin categoría';
            if (!grouped[category]) {
                grouped[category] = 0;
            }
            grouped[category] += sale.total;
        });
        
        return grouped;
    }

    private groupInventoryByCategory(inventory: InventoryItem[]): Record<string, { count: number; value: number }> {
        const grouped: Record<string, { count: number; value: number }> = {};
        
        inventory.forEach(item => {
            if (!grouped[item.category]) {
                grouped[item.category] = { count: 0, value: 0 };
            }
            grouped[item.category].count += 1;
            grouped[item.category].value += item.quantity * item.cost;
        });
        
        return grouped;
    }

    private categorizeInventoryStatus(inventory: InventoryItem[]): { sufficient: number; low: number; critical: number } {
        const status = { sufficient: 0, low: 0, critical: 0 };
        
        inventory.forEach(item => {
            const ratio = item.quantity / item.maxQuantity;
            if (ratio <= 0.1) {
                status.critical++;
            } else if (ratio <= 0.3) {
                status.low++;
            } else {
                status.sufficient++;
            }
        });
        
        return status;
    }

    private getTopProducts(sales: SaleItem[], limit: number = 5): { name: string; revenue: number }[] {
        const productRevenue: Record<string, number> = {};
        
        sales.forEach(sale => {
            if (!productRevenue[sale.productName]) {
                productRevenue[sale.productName] = 0;
            }
            productRevenue[sale.productName] += sale.total;
        });
        
        return Object.entries(productRevenue)
            .sort(([, a], [, b]) => b - a)
            .slice(0, limit)
            .map(([name, revenue]) => ({ name, revenue }));
    }

    // Chart rendering
    private renderChart(containerId: string, chartData: PlotlyData): void {
        const container = document.getElementById(containerId);
        if (!container || !window.Plotly) return;

        try {
            window.Plotly.newPlot(container, chartData.data, chartData.layout, chartData.config);
            this.charts.set(containerId, { container, data: chartData });
        } catch (error) {
            console.error(`Error rendering chart in ${containerId}:`, error);
        }
    }

    private refreshSalesAnalytics(): void {
        this.loadSalesAnalytics();
    }

    private refreshInventoryAnalytics(): void {
        this.loadInventoryAnalytics();
    }

    private refreshRecipeAnalytics(): void {
        this.loadRecipeAnalytics();
    }

    // Export chart as image
    async exportChart(containerId: string, format: 'png' | 'jpeg' | 'svg' = 'png'): Promise<string | null> {
        const chart = this.charts.get(containerId);
        if (!chart || !window.Plotly) return null;

        try {
            const imageData = await window.Plotly.toImage(chart.container, {
                format,
                width: 800,
                height: 600
            });
            return imageData;
        } catch (error) {
            console.error(`Error exporting chart ${containerId}:`, error);
            return null;
        }
    }

    // Data export for charts
    exportChartData(containerId: string): any | null {
        const chart = this.charts.get(containerId);
        return chart ? chart.data : null;
    }
}

// Create singleton instance
const analyticsManager = new AnalyticsManager();

// Export for use in other modules
export { AnalyticsManager, analyticsManager };

// Make available globally
declare global {
    interface Window {
        analyticsManager: AnalyticsManager;
        loadSalesAnalytics: typeof analyticsManager.loadSalesAnalytics;
        loadInventoryAnalytics: typeof analyticsManager.loadInventoryAnalytics;
        loadRecipeAnalytics: typeof analyticsManager.loadRecipeAnalytics;
    }
}

window.analyticsManager = analyticsManager;
window.loadSalesAnalytics = () => analyticsManager.loadSalesAnalytics();
window.loadInventoryAnalytics = () => analyticsManager.loadInventoryAnalytics();
window.loadRecipeAnalytics = () => analyticsManager.loadRecipeAnalytics();