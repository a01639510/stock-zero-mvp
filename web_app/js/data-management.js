// Stock Zero - Data Management JavaScript

// ==============================
// 📦 DATA MANAGEMENT FUNCTIONS
// ==============================

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const fileType = event.target.id === 'salesFile' ? 'sales' : 'inventory';
    showNotification(`Procesando archivo ${file.name}...`, 'info');

    Papa.parse(file, {
        header: true,
        complete: function (results) {
            if (results.data && results.data.length > 0) {
                appState.data[fileType] = results.data;
                saveData();
                updateDataPreview(fileType, results.data);
                showNotification(
                    `Archivo ${fileType} importado exitosamente (${results.data.length} registros)`,
                    'success'
                );

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
        error: function (error) {
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

    const csv = Papa.unparse(data);
    downloadFile(csv, filename, 'text/csv');
    showNotification(`Datos exportados como ${filename}`, 'success');
}

// ==============================
// 🧪 SAMPLE DATA GENERATION
// ==============================

function generateSampleData() {
    showNotification('Generando datos de ejemplo...', 'info');

    // Datos de ejemplo de inventario
    const sampleInventory = [
        { producto: 'Café Americano', stock_actual: 25, stock_minimo: 10, stock_optimo: 30 },
        { producto: 'Capuchino', stock_actual: 8, stock_minimo: 10, stock_optimo: 25 },
        { producto: 'Croissant', stock_actual: 15, stock_minimo: 5, stock_optimo: 20 },
        { producto: 'Leche Deslactosada', stock_actual: 5, stock_minimo: 8, stock_optimo: 15 },
        { producto: 'Azúcar Morena', stock_actual: 18, stock_minimo: 5, stock_optimo: 20 }
    ];

    // Datos de ejemplo de ventas (últimos días)
    const sampleSales = [
        { producto: 'Café Americano', fecha: '2025-11-01', ventas: 45.00 },
        { producto: 'Capuchino', fecha: '2025-11-01', ventas: 55.00 },
        { producto: 'Croissant', fecha: '2025-11-02', ventas: 25.00 },
        { producto: 'Leche Deslactosada', fecha: '2025-11-02', ventas: 30.00 },
        { producto: 'Café Americano', fecha: '2025-11-03', ventas: 45.00 },
        { producto: 'Croissant', fecha: '2025-11-03', ventas: 25.00 },
        { producto: 'Capuchino', fecha: '2025-11-04', ventas: 55.00 }
    ];

    // Actualiza el estado global
    appState.data = {
        sales: sampleSales,
        inventory: sampleInventory
    };

    saveData();

    // Actualiza la vista previa
    updateDataPreview('sales', sampleSales);
    updateDataPreview('inventory', sampleInventory);

    showNotification('Datos de ejemplo generados exitosamente', 'success');

    // Refresca dashboard si está abierto
    if (appState.currentTab === 'dashboard') {
        loadDashboard();
    }
}

// ==============================
// 👀 DATA PREVIEW
// ==============================

function updateDataPreview(type, data) {
    const container = document.getElementById('dataPreview');

    if (!container) return;

    if (!data || data.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No hay datos disponibles</p>';
        return;
    }

    const headers = Object.keys(data[0]);
    const rows = data.slice(0, 10);

    let html = `
        <div class="mb-4">
            <h4 class="text-md font-medium text-gray-900 mb-2">
                ${type === 'sales' ? 'Ventas' : 'Inventario'} (${data.length} registros)
            </h4>
        </div>
        <table class="data-table">
            <thead>
                <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${rows
                    .map(row => `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`)
                    .join('')}
            </tbody>
        </table>
    `;

    if (data.length > 10) {
        html += `<p class="text-sm text-gray-500 mt-4">Mostrando primeros 10 registros de ${data.length} totales</p>`;
    }

    container.innerHTML = html;
}

// ==============================
// 💾 FILE DOWNLOAD
// ==============================

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

// ==============================
// 📊 REPORT GENERATION
// ==============================

function generatePDFReport() {
    showNotification('Generando reporte PDF...', 'info');

    setTimeout(() => {
        const reportContent = generateReportContent();
        const printWindow = window.open('', '_blank');
        printWindow.document.write(reportContent);
        printWindow.document.close();
        printWindow.onload = function () {
            printWindow.print();
        };
        showNotification('Reporte generado para impresión', 'success');
    }, 1200);
}

function generateReportContent() {
    const kpis = appState.kpis || {
        totalSales: 2300,
        criticalProducts: 2,
        efficiency: 92.5,
        inventoryValue: 4500
    };

    const sales = appState.data.sales || [];
    const inventory = appState.data.inventory || [];

    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Stock Zero Reporte</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
                .kpi-card { border: 1px solid #ddd; padding: 15px; text-align: center; border-radius: 8px; }
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
                        const stock = Number(item.stock_actual);
                        const min = Number(item.stock_minimo);
                        const opt = Number(item.stock_optimo);

                        const status =
                            stock <= min ? 'Crítico' :
                            stock >= opt ? 'Óptimo' :
                            'Normal';

                        const color =
                            status === 'Crítico' ? 'red' :
                            status === 'Óptimo' ? 'green' :
                            'orange';

                        return `
                            <tr>
                                <td>${item.producto}</td>
                                <td>${stock}</td>
                                <td>${min}</td>
                                <td>${opt}</td>
                                <td style="color:${color};font-weight:bold;">${status}</td>
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
                        sales.reduce((acc, s) => {
                            const prod = s.producto || 'Desconocido';
                            if (!acc[prod]) acc[prod] = { units: 0, total: 0 };
                            acc[prod].units += 1;
                            acc[prod].total += parseFloat(s.ventas || 0);
                            return acc;
                        }, {})
                    )
                        .map(([prod, d]) => `
                            <tr>
                                <td>${prod}</td>
                                <td>${d.units}</td>
                                <td>${formatCurrency(d.total)}</td>
                            </tr>
                        `)
                        .join('')}
                </tbody>
            </table>

            <div class="footer">
                <p>Reporte generado por Stock Zero - Sistema Inteligente de Gestión</p>
            </div>
        </body>
        </html>
    `;
}

// ==============================
// ⚙️ LOAD TAB
// ==============================

function loadDataManagement() {
    console.log('Loading data management...');

    if (appState.data.sales && appState.data.sales.length > 0) {
        updateDataPreview('sales', appState.data.sales);
    }

    if (appState.data.inventory && appState.data.inventory.length > 0) {
        updateDataPreview('inventory', appState.data.inventory);
    }

    const salesFile = document.getElementById('salesFile');
    const inventoryFile = document.getElementById('inventoryFile');

    if (salesFile) salesFile.addEventListener('change', handleFileUpload);
    if (inventoryFile) inventoryFile.addEventListener('change', handleFileUpload);
}

// ==============================
// 💲 UTILITY
// ==============================

function formatCurrency(value) {
    return `$${Number(value || 0).toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}
