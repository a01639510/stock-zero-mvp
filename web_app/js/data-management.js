// Stock Zero - Data Management JavaScript

// Data Management Functions
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileType = event.target.id === 'salesFile' ? 'sales' : 'inventory';
    
    showNotification(`Procesando archivo ${file.name}...`, 'info');
    
    Papa.parse(file, {
        header: true,
        complete: function(results) {
            if (results.data && results.data.length > 0) {
                appState.data[fileType] = results.data;
                saveData();
                updateDataPreview(fileType, results.data);
                showNotification(`Archivo ${fileType} importado exitosamente (${results.data.length} registros)`, 'success');
                
                // Refresh current view
                if (appState.currentTab === 'data') {
                    loadDataManagement();
                } else if (appState.currentTab === 'dashboard') {
                    loadDashboard();
                }
            } else {
                showNotification('El archivo está vacío o tiene un formato inválido', 'error');
            }
        },
        error: function(error) {
            showNotification(`Error al procesar el archivo: ${error.message}`, 'error');
        }
    });
}

function importData() {
    const salesFile = document.getElementById('salesFile').files[0];
    const inventoryFile = document.getElementById('inventoryFile').files[0];
    
    if (!salesFile && !inventoryFile) {
        showNotification('Por favor, selecciona al menos un archivo para importar', 'warning');
        return;
    }
    
    showNotification('Importando datos...', 'info');
    
    // Process files if they exist
    if (salesFile) {
        handleFileUpload({ target: { id: 'salesFile', files: [salesFile] } });
    }
    
    if (inventoryFile) {
        handleFileUpload({ target: { id: 'inventoryFile', files: [inventoryFile] } });
    }
}

function exportData(type) {
    let data, filename, content;
    
    switch (type) {
        case 'sales':
            data = appState.data.sales;
            filename = `ventas_${new Date().toISOString().split('T')[0]}.csv`;
            break;
        case 'inventory':
            data = appState.data.inventory;
            filename = `inventario_${new Date().toISOString().split('T')[0]}.csv`;
            break;
        case 'report':
            generatePDFReport();
            return;
        default:
            data = { ...appState.data };
            filename = `stock_zero_data_${new Date().toISOString().split('T')[0]}.json`;
            content = JSON.stringify(data, null, 2);
            downloadFile(content, filename, 'application/json');
            return;
    }
    
    if (!data || data.length === 0) {
        showNotification('No hay datos disponibles para exportar', 'warning');
        return;
    }
    
    // Convert to CSV
    const csv = Papa.unparse(data);
    downloadFile(csv, filename, 'text/csv');
    showNotification(`Datos exportados como ${filename}`, 'success');
}

function generateSampleData() {
    showNotification('Generando datos de ejemplo...', 'info');
    
    const sampleData = generateSampleData();
    appState.data = sampleData;
    saveData();
    
    // Update preview
    updateDataPreview('sales', sampleData.sales);
    updateDataPreview('inventory', sampleData.inventory);
    
    showNotification('Datos de ejemplo generados exitosamente', 'success');
    
    // Refresh current view
    if (appState.currentTab === 'dashboard') {
        loadDashboard();
    }
}

function updateDataPreview(type, data) {
    const container = document.getElementById('dataPreview');
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No hay datos disponibles</p>';
        return;
    }
    
    // Create table preview
    const headers = Object.keys(data[0]);
    const rows = data.slice(0, 10); // Show first 10 rows
    
    let html = `
        <div class="mb-4">
            <h4 class="text-md font-medium text-gray-900 mb-2">
                ${type === 'sales' ? 'Ventas' : 'Inventario'} (${data.length} registros)
            </h4>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    ${headers.map(header => `<th>${header}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${rows.map(row => `
                    <tr>
                        ${headers.map(header => `<td>${row[header] || ''}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    if (data.length > 10) {
        html += `<p class="text-sm text-gray-500 mt-4">Mostrando primeros 10 registros de ${data.length} totales</p>`;
    }
    
    container.innerHTML = html;
}

function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

function generatePDFReport() {
    showNotification('Generando reporte PDF...', 'info');
    
    // This is a simplified version - in a real implementation you would use a PDF library
    setTimeout(() => {
        const reportContent = generateReportContent();
        const filename = `stock_zero_report_${new Date().toISOString().split('T')[0]}.html`;
        
        // Open in new window for printing
        const printWindow = window.open('', '_blank');
        printWindow.document.write(reportContent);
        printWindow.document.close();
        
        printWindow.onload = function() {
            printWindow.print();
        };
        
        showNotification('Reporte generado para impresión', 'success');
    }, 1500);
}

function generateReportContent() {
    const kpis = appState.kpis;
    const sales = appState.data.sales;
    const inventory = appState.data.inventory;
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Stock Zero Reporte</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
                .kpi-card { border: 1px solid #ddd; padding: 15px; text-align: center; }
                .kpi-value { font-size: 24px; font-weight: bold; color: #3B82F6; }
                .kpi-label { font-size: 14px; color: #666; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f5f5f5; font-weight: bold; }
                .footer { margin-top: 30px; text-align: center; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏭 Stock Zero - Reporte de Gestión</h1>
                <p>Generado el ${new Date().toLocaleDateString('es-MX')}</p>
            </div>
            
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">${formatCurrency(kpis.totalSales)}</div>
                    <div class="kpi-label">Ventas Totales</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${kpis.criticalProducts}</div>
                    <div class="kpi-label">Productos Críticos</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${kpis.efficiency.toFixed(1)}%</div>
                    <div class="kpi-label">Eficiencia</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${formatCurrency(kpis.inventoryValue)}</div>
                    <div class="kpi-label">Valor Inventario</div>
                </div>
            </div>
            
            <h2>Estado del Inventario</h2>
            <table>
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Stock Actual</th>
                        <th>Stock Mínimo</th>
                        <th>Stock Óptimo</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    ${inventory.map(item => {
                        const status = item.stock_actual <= item.stock_minimo ? 'Crítico' : 
                                      item.stock_actual >= item.stock_optimo ? 'Óptimo' : 'Normal';
                        const statusColor = status === 'Crítico' ? 'red' : 
                                          status === 'Óptimo' ? 'green' : 'orange';
                        
                        return `
                            <tr>
                                <td>${item.producto}</td>
                                <td>${item.stock_actual}</td>
                                <td>${item.stock_minimo}</td>
                                <td>${item.stock_optimo}</td>
                                <td style="color: ${statusColor}; font-weight: bold;">${status}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
            
            <h2>Resumen de Ventas (Últimos 30 días)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Unidades Vendidas</th>
                        <th>Total Ventas</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(
                        sales.reduce((acc, sale) => {
                            if (!acc[sale.producto]) {
                                acc[sale.producto] = { units: 0, total: 0 };
                            }
                            acc[sale.producto].units += 1;
                            acc[sale.producto].total += parseFloat(sale.ventas || 0);
                            return acc;
                        }, {})
                    ).map(([product, data]) => `
                        <tr>
                            <td>${product}</td>
                            <td>${data.units}</td>
                            <td>${formatCurrency(data.total)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            
            <div class="footer">
                <p>Reporte generado por Stock Zero - Sistema Inteligente de Gestión</p>
            </div>
        </body>
        </html>
    `;
}

// Data Management Tab Functions
function loadDataManagement() {
    console.log('Loading data management...');
    
    // Update preview with current data
    if (appState.data.sales.length > 0) {
        updateDataPreview('sales', appState.data.sales);
    }
    
    if (appState.data.inventory.length > 0) {
        updateDataPreview('inventory', appState.data.inventory);
    }
    
    // Set up file upload listeners
    const salesFile = document.getElementById('salesFile');
    const inventoryFile = document.getElementById('inventoryFile');
    
    if (salesFile) {
        salesFile.addEventListener('change', handleFileUpload);
    }
    
    if (inventoryFile) {
        inventoryFile.addEventListener('change', handleFileUpload);
    }
}