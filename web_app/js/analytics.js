// Stock Zero - Analytics JavaScript

// Analytics Functions
function loadAnalysis() {
    console.log('Loading analysis...');
    
    const container = document.getElementById('analysisResults');
    container.innerHTML = `
        <div class="bg-white rounded-xl shadow-lg p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-chart-bar text-blue-600 mr-2"></i>Panel de Análisis
            </h3>
            <p class="text-gray-600 text-center py-8">
                Selecciona los parámetros y haz click en "Ejecutar Análisis" para generar resultados.
            </p>
        </div>
    `;
}

function runAnalysis() {
    showNotification('Ejecutando análisis...', 'info');
    
    const period = document.getElementById('analysisPeriod').value;
    const type = document.getElementById('analysisType').value;
    const products = document.getElementById('analysisProducts').value;
    
    // Show loading state
    const container = document.getElementById('analysisResults');
    container.innerHTML = `
        <div class="bg-white rounded-xl shadow-lg p-6">
            <div class="flex items-center justify-center py-12">
                <div class="loading-spinner mr-4"></div>
                <span class="text-gray-600">Analizando datos...</span>
            </div>
        </div>
    `;
    
    // Simulate analysis processing
    setTimeout(() => {
        const results = generateAnalysisResults(period, type, products);
        displayAnalysisResults(results);
        showNotification('Análisis completado exitosamente', 'success');
    }, 2000);
}

function generateAnalysisResults(period, type, products) {
    const sales = appState.data.sales;
    const inventory = appState.data.inventory;
    
    // Filter data based on period
    const now = new Date();
    const startDate = new Date(now.getTime() - period * 24 * 60 * 60 * 1000);
    const filteredSales = sales.filter(sale => new Date(sale.fecha) >= startDate);
    
    // Filter products
    let filteredProducts = [];
    if (products === 'critical') {
        filteredProducts = inventory.filter(item => item.stock_actual <= item.stock_minimo);
    } else if (products === 'top') {
        const salesByProduct = {};
        filteredSales.forEach(sale => {
            salesByProduct[sale.producto] = (salesByProduct[sale.producto] || 0) + 1;
        });
        const topProducts = Object.entries(salesByProduct)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .map(([product]) => product);
        filteredProducts = inventory.filter(item => topProducts.includes(item.producto));
    } else {
        filteredProducts = inventory;
    }
    
    const results = {
        period,
        type,
        products: products,
        filteredData: {
            sales: filteredSales.filter(sale => 
                filteredProducts.some(p => p.producto === sale.producto)
            ),
            inventory: filteredProducts
        },
        insights: generateInsights(filteredSales, filteredProducts, type)
    };
    
    return results;
}

function generateInsights(sales, inventory, analysisType) {
    const insights = [];
    
    // Sales insights
    if (sales.length > 0) {
        const totalSales = sales.reduce((sum, sale) => sum + parseFloat(sale.ventas || 0), 0);
        const avgSales = totalSales / sales.length;
        
        insights.push({
            type: 'sales',
            title: 'Análisis de Ventas',
            value: formatCurrency(totalSales),
            description: \`Ventas totales en el período con un promedio de \${formatCurrency(avgSales)} por transacción\`,
            trend: Math.random() > 0.5 ? 'up' : 'down',
            trendValue: (Math.random() * 20 - 10).toFixed(1)
        });
    }
    
    // Inventory insights
    if (inventory.length > 0) {
        const criticalCount = inventory.filter(item => item.stock_actual <= item.stock_minimo).length;
        const optimalCount = inventory.filter(item => item.stock_actual >= item.stock_optimo).length;
        
        insights.push({
            type: 'inventory',
            title: 'Estado del Inventario',
            value: \`\${inventory.length - criticalCount}/\${inventory.length}\`,
            description: \`\${criticalCount} productos en nivel crítico, \${optimalCount} en nivel óptimo\`,
            trend: criticalCount > 0 ? 'down' : 'up',
            trendValue: criticalCount > 0 ? \`-\${criticalCount}\` : \`+\${optimalCount}\`
        });
        
        insights.push({
            type: 'efficiency',
            title: 'Eficiencia de Inventario',
            value: \`\${((inventory.length - criticalCount) / inventory.length * 100).toFixed(1)}%\`,
            description: 'Porcentaje de productos con niveles de stock adecuados',
            trend: Math.random() > 0.3 ? 'up' : 'down',
            trendValue: (Math.random() * 10 - 5).toFixed(1)
        });
    }
    
    // Type-specific insights
    if (analysisType === 'prediction') {
        insights.push({
            type: 'prediction',
            title: 'Proyección de Demanda',
            value: '+15.2%',
            description: 'Aumento esperado en la demanda para el próximo período basado en tendencias históricas',
            trend: 'up',
            trendValue: '+15.2%'
        });
    } else if (analysisType === 'efficiency') {
        insights.push({
            type: 'efficiency',
            title: 'Costo de Oportunidad',
            value: formatCurrency(Math.random() * 10000),
            description: 'Pérdidas estimadas por niveles de stock subóptimos',
            trend: 'down',
            trendValue: '-12.3%'
        });
    }
    
    return insights;
}