declare class AnalyticsManager {
    private charts;
    private colors;
    constructor();
    private initializeEventListeners;
    loadDashboardKPIs(): Promise<void>;
    private updateKPICards;
    private updateKPICard;
    private loadDashboardCharts;
    loadSalesAnalytics(): Promise<void>;
    private createSalesTrendChart;
    private createSalesByCategoryChart;
    loadInventoryAnalytics(): Promise<void>;
    private createInventoryStatusChart;
    private createInventoryByCategoryChart;
    loadRecipeAnalytics(): Promise<void>;
    private createRecipeProfitabilityChart;
    private createTopProductsChart;
    private groupSalesByDate;
    private groupSalesByCategory;
    private groupInventoryByCategory;
    private categorizeInventoryStatus;
    private getTopProducts;
    private renderChart;
    private refreshSalesAnalytics;
    private refreshInventoryAnalytics;
    private refreshRecipeAnalytics;
    exportChart(containerId: string, format?: 'png' | 'jpeg' | 'svg'): Promise<string | null>;
    exportChartData(containerId: string): any | null;
}
declare const analyticsManager: AnalyticsManager;
export { AnalyticsManager, analyticsManager };
declare global {
    interface Window {
        analyticsManager: AnalyticsManager;
        loadSalesAnalytics: typeof analyticsManager.loadSalesAnalytics;
        loadInventoryAnalytics: typeof analyticsManager.loadInventoryAnalytics;
        loadRecipeAnalytics: typeof analyticsManager.loadRecipeAnalytics;
    }
}
//# sourceMappingURL=analytics.d.ts.map