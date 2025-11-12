// Stock Zero - Optimization JavaScript

// Optimization Functions
function loadOptimization() {
    console.log('Loading optimization...');
    
    const container = document.getElementById('optimizationResults');
    container.innerHTML = `
        <div class="bg-white rounded-xl shadow-lg p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-cogs text-green-600 mr-2"></i>Resultados de Optimización
            </h3>
            <p class="text-gray-600 text-center py-8">
                Configura los parámetros de optimización y haz click en "Ejecutar Optimización" para generar recomendaciones.
            </p>
        </div>
    `;
}

function runOptimization() {
    showNotification('Ejecutando optimización inteligente...', 'info');
    
    const serviceLevel = parseFloat(document.getElementById('serviceLevel').value);
    const leadTime = parseInt(document.getElementById('leadTime').value);
    const holdingCost = parseFloat(document.getElementById('holdingCost').value);
    
    const objectives = {
        optimizeStock: document.getElementById('optimizeStock').checked,
        optimizeOrders: document.getElementById('optimizeOrders').checked,
        reduceCosts: document.getElementById('reduceCosts').checked,
        improveService: document.getElementById('improveService').checked
    };
    
    // Show loading state
    const container = document.getElementById('optimizationResults');
    container.innerHTML = `
        <div class="bg-white rounded-xl shadow-lg p-6">
            <div class="flex items-center justify-center py-12">
                <div class="loading-spinner mr-4"></div>
                <span class="text-gray-600">Optimizando parámetros...</span>
            </div>
        </div>
    `;
    
    // Simulate optimization processing
    setTimeout(() => {
        const results = generateOptimizationResults(serviceLevel, leadTime, holdingCost, objectives);
        displayOptimizationResults(results);
        showNotification('Optimización completada exitosamente', 'success');
    }, 3000);
}

function generateOptimizationResults(serviceLevel, leadTime, holdingCost, objectives) {
    const inventory = appState.data.inventory;
    const sales = appState.data.sales;
    
    const results = {
        parameters: { serviceLevel, leadTime, holdingCost, objectives },
        recommendations: [],
        savings: { estimated: 0, categories: {} },
        implementation: []
    };
    
    // Generate recommendations for each product
    inventory.forEach(item => {
        const currentStock = parseInt(item.stock_actual);
        const minStock = parseInt(item.stock_minimo);
        const optimalStock = parseInt(item.stock_optimo);
        
        // Calculate optimal order quantity using EOQ formula (simplified)
        const demand = estimateDemand(sales, item.producto);
        const orderCost = 50; // Fixed order cost
        const eoq = Math.sqrt((2 * demand * orderCost) / (holdingCost / 100));
        
        // Calculate safety stock
        const demandVariability = calculateDemandVariability(sales, item.producto);
        const safetyStock = Math.ceil(demandVariability * serviceLevel / 100);
        
        // Calculate reorder point
        const reorderPoint = Math.ceil(demand / 30 * leadTime) + safetyStock;
        
        const recommendation = {
            product: item.producto,
            current: currentStock,
            recommended: {
                reorderPoint: reorderPoint,
                orderQuantity: Math.round(eoq),
                safetyStock: safetyStock,
                maxStock: Math.max(optimalStock, reorderPoint + Math.round(eoq))
            },
            priority: currentStock <= minStock ? 'high' : currentStock <= optimalStock ? 'medium' : 'low',
            estimatedSavings: calculateSavings(currentStock, reorderPoint, Math.round(eoq), holdingCost)
        };
        
        results.recommendations.push(recommendation);
    });
    
    // Calculate total estimated savings
    results.savings.estimated = results.recommendations.reduce((sum, rec) => sum + rec.estimatedSavings, 0);
    
    // Generate implementation plan
    results.implementation = generateImplementationPlan(results.recommendations);
    
    // Generate additional insights
    if (objectives.optimizeStock) {
        results.savings.categories.stock = results.savings.estimated * 0.4;
    }
    if (objectives.optimizeOrders) {
        results.savings.categories.orders = results.savings.estimated * 0.3;
    }
    if (objectives.reduceCosts) {
        results.savings.categories.costs = results.savings.estimated * 0.2;
    }
    if (objectives.improveService) {
        results.savings.categories.service = results.savings.estimated * 0.1;
    }
    
    return results;
}

function estimateDemand(sales, productName) {
    const productSales = sales.filter(sale => sale.producto === productName);
    if (productSales.length === 0) return 100; // Default demand
    
    // Calculate daily demand from last 30 days
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const recentSales = productSales.filter(sale => new Date(sale.fecha) >= thirtyDaysAgo);
    
    return recentSales.reduce((sum, sale) => sum + parseFloat(sale.ventas || 0), 0);
}

function calculateDemandVariability(sales, productName) {
    const productSales = sales.filter(sale => sale.producto === productName);
    if (productSales.length < 2) return 10; // Default variability
    
    const values = productSales.map(sale => parseFloat(sale.ventas || 0));
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    
    return Math.sqrt(variance);
}

function calculateSavings(currentStock, reorderPoint, orderQuantity, holdingCost) {
    // Simplified savings calculation
    const optimalValue = reorderPoint + orderQuantity;
    const currentValue = currentStock;
    const difference = Math.abs(currentValue - optimalValue);
    
    return difference * holdingCost / 100 * 0.1; // 10% of holding cost as potential savings
}

function generateImplementationPlan(recommendations) {
    const highPriority = recommendations.filter(rec => rec.priority === 'high');
    const mediumPriority = recommendations.filter(rec => rec.priority === 'medium');
    const lowPriority = recommendations.filter(rec => rec.priority === 'low');
    
    const plan = [
        {
            phase: 'Fase 1: Acción Inmediata (Próximos 7 días)',
            tasks: highPriority.slice(0, 3).map(rec => ({
                action: \`Reabastecer \${rec.producto}\`,
                description: \`Ordenar \${rec.recommended.orderQuantity} unidades, punto de reorden: \${rec.recommended.reorderPoint}\`,
                priority: 'Alta',
                estimatedImpact: formatCurrency(rec.estimatedSavings)
            }))
        },
        {
            phase: 'Fase 2: Optimización Corto Plazo (Próximos 30 días)',
            tasks: mediumPriority.slice(0, 5).map(rec => ({
                action: \`Optimizar \${rec.producto}\`,
                description: \`Ajustar niveles de stock, implementar punto de reorden en \${rec.recommended.reorderPoint}\`,
                priority: 'Media',
                estimatedImpact: formatCurrency(rec.estimatedSavings)
            }))
        },
        {
            phase: 'Fase 3: Mejora Continua (Próximos 90 días)',
            tasks: lowPriority.slice(0, 3).map(rec => ({
                action: \`Monitorear \${rec.producto}\`,
                description: \`Implementar sistema de monitoreo, ajustar según tendencias\`,
                priority: 'Baja',
                estimatedImpact: formatCurrency(rec.estimatedSavings)
            }))
        }
    ];
    
    return plan;
}

function displayOptimizationResults(results) {
    const container = document.getElementById('optimizationResults');
    
    // Summary Card
    const summaryHTML = `
        <div class="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl shadow-lg p-6 mb-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="text-center">
                    <h4 class="text-lg font-semibold text-gray-900 mb-2">Ahorro Estimado</h4>
                    <p class="text-3xl font-bold text-green-600">${formatCurrency(results.savings.estimated)}</p>
                    <p class="text-sm text-gray-600">Anual proyectado</p>
                </div>
                <div class="text-center">
                    <h4 class="text-lg font-semibold text-gray-900 mb-2">Productos Optimizados</h4>
                    <p class="text-3xl font-bold text-blue-600">${results.recommendations.length}</p>
                    <p class="text-sm text-gray-600">Con recomendaciones</p>
                </div>
                <div class="text-center">
                    <h4 class="text-lg font-semibold text-gray-900 mb-2">Prioridad Alta</h4>
                    <p class="text-3xl font-bold text-orange-600">${results.recommendations.filter(r => r.priority === 'high').length}</p>
                    <p class="text-sm text-gray-600">Requieren acción inmediata</p>
                </div>
            </div>
        </div>
    `;
    
    // Recommendations Table
    const recommendationsHTML = `
        <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-clipboard-list text-green-600 mr-2"></i>Recomendaciones por Producto
            </h3>
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Stock Actual</th>
                            <th>Punto de Reorden</th>
                            <th>Cantidad de Pedido</th>
                            <th>Stock de Seguridad</th>
                            <th>Prioridad</th>
                            <th>Ahorro Estimado</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${results.recommendations.map(rec => `
                            <tr>
                                <td class="font-medium">${rec.product}</td>
                                <td>${rec.current}</td>
                                <td class="font-semibold text-orange-600">${rec.recommended.reorderPoint}</td>
                                <td class="font-semibold text-blue-600">${rec.recommended.orderQuantity}</td>
                                <td>${rec.recommended.safetyStock}</td>
                                <td>
                                    <span class="status-badge status-badge-${rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'success'}">
                                        ${rec.priority === 'high' ? 'Alta' : rec.priority === 'medium' ? 'Media' : 'Baja'}
                                    </span>
                                </td>
                                <td class="font-semibold text-green-600">${formatCurrency(rec.estimatedSavings)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    // Implementation Plan
    const implementationHTML = `
        <div class="bg-white rounded-xl shadow-lg p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-project-diagram text-blue-600 mr-2"></i>Plan de Implementación
            </h3>
            <div class="space-y-6">
                ${results.implementation.map(phase => `
                    <div class="border-l-4 border-blue-500 pl-4">
                        <h4 class="text-md font-semibold text-gray-900 mb-3">${phase.phase}</h4>
                        <div class="space-y-2">
                            ${phase.tasks.map(task => `
                                <div class="bg-gray-50 rounded-lg p-3">
                                    <div class="flex justify-between items-start">
                                        <div class="flex-1">
                                            <p class="font-medium text-gray-900">${task.action}</p>
                                            <p class="text-sm text-gray-600 mt-1">${task.description}</p>
                                        </div>
                                        <div class="ml-4 text-right">
                                            <span class="status-badge status-badge-${task.priority === 'Alta' ? 'danger' : task.priority === 'Media' ? 'warning' : 'success'} text-xs">
                                                ${task.priority}
                                            </span>
                                            <p class="text-sm font-semibold text-green-600 mt-1">${task.estimatedImpact}</p>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    container.innerHTML = summaryHTML + recommendationsHTML + implementationHTML;
}

// Utility function for optimization calculations
function calculateEOQ(demand, orderCost, holdingCost) {
    return Math.sqrt((2 * demand * orderCost) / holdingCost);
}

function calculateServiceFactor(serviceLevel) {
    // Simplified service factor calculation
    const zScores = {
        80: 0.84,
        85: 1.04,
        90: 1.28,
        95: 1.65,
        99: 2.33
    };
    
    return zScores[serviceLevel] || 1.65;
}