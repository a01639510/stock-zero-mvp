// Stock Zero - Recipes Management JavaScript

// Recipes Functions
function loadRecipes() {
    console.log('Loading recipes...');
    
    updateRecipesList();
    updateRecipeSelect();
}

function updateRecipesList() {
    const container = document.getElementById('recipesList');
    const recipes = appState.data.recipes;
    
    if (recipes.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-utensils text-gray-400 text-4xl mb-4"></i>
                <p class="text-gray-600">No hay recetas configuradas</p>
                <button onclick="addNewRecipe()" class="mt-4 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors">
                    <i class="fas fa-plus mr-2"></i>Agregar Primera Receta
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = recipes.map(recipe => createRecipeCard(recipe)).join('');
}

function createRecipeCard(recipe) {
    return `
        <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div class="flex justify-between items-start mb-4">
                <h4 class="text-lg font-semibold text-gray-900">${recipe.name}</h4>
                <div class="flex space-x-2">
                    <button onclick="editRecipe(${recipe.id})" class="text-blue-600 hover:text-blue-800">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteRecipe(${recipe.id})" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <p class="text-sm text-gray-600 mb-4">${recipe.description}</p>
            
            <div class="border-t pt-4">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-medium text-gray-700">Rendimiento:</span>
                    <span class="text-sm font-semibold">${recipe.yield} ${recipe.unit}</span>
                </div>
                
                <div class="mb-3">
                    <span class="text-sm font-medium text-gray-700">Ingredientes:</span>
                    <ul class="text-xs text-gray-600 mt-1 space-y-1">
                        ${recipe.ingredients.slice(0, 3).map(ing => 
                            `<li>• ${ing.name}: ${ing.quantity} ${ing.unit}</li>`
                        ).join('')}
                        ${recipe.ingredients.length > 3 ? `<li>• ... y ${recipe.ingredients.length - 3} más</li>` : ''}
                    </ul>
                </div>
                
                <button onclick="selectRecipeForCalculation(${recipe.id})" 
                    class="w-full bg-orange-100 text-orange-700 px-3 py-2 rounded-lg hover:bg-orange-200 transition-colors text-sm font-medium">
                    <i class="fas fa-calculator mr-2"></i>Calcular Ingredientes
                </button>
            </div>
        </div>
    `;
}

function updateRecipeSelect() {
    const select = document.getElementById('recipeSelect');
    const recipes = appState.data.recipes;
    
    select.innerHTML = '<option value="">Selecciona una receta...</option>' +
        recipes.map(recipe => 
            `<option value="${recipe.id}">${recipe.name}</option>`
        ).join('');
}

function addNewRecipe() {
    const newRecipe = {
        id: Date.now(),
        name: 'Nueva Receta',
        description: 'Descripción de la nueva receta',
        ingredients: [
            { name: 'Ingrediente A', quantity: 10, unit: 'kg' },
            { name: 'Ingrediente B', quantity: 5, unit: 'kg' }
        ],
        yield: 100,
        unit: 'unidades'
    };
    
    appState.data.recipes.push(newRecipe);
    saveData();
    updateRecipesList();
    updateRecipeSelect();
    
    showNotification('Nueva receta agregada. Edita los detalles según necesites.', 'success');
}

function editRecipe(recipeId) {
    const recipe = appState.data.recipes.find(r => r.id === recipeId);
    if (!recipe) return;
    
    // Simple edit - in a real implementation this would open a modal
    const newName = prompt('Nombre de la receta:', recipe.name);
    if (newName && newName.trim()) {
        recipe.name = newName.trim();
        saveData();
        updateRecipesList();
        updateRecipeSelect();
        showNotification('Receta actualizada exitosamente', 'success');
    }
}

function deleteRecipe(recipeId) {
    if (confirm('¿Estás seguro de que quieres eliminar esta receta?')) {
        appState.data.recipes = appState.data.recipes.filter(r => r.id !== recipeId);
        saveData();
        updateRecipesList();
        updateRecipeSelect();
        showNotification('Receta eliminada exitosamente', 'success');
    }
}

function selectRecipeForCalculation(recipeId) {
    document.getElementById('recipeSelect').value = recipeId;
    document.getElementById('recipeQuantity').value = 100;
    
    // Scroll to calculator
    document.getElementById('recipesContent').scrollIntoView({ behavior: 'smooth' });
    
    calculateIngredients();
}

function calculateIngredients() {
    const recipeId = parseInt(document.getElementById('recipeSelect').value);
    const quantity = parseInt(document.getElementById('recipeQuantity').value);
    const period = parseInt(document.getElementById('recipePeriod').value);
    
    if (!recipeId || !quantity) {
        showNotification('Por favor, selecciona una receta y cantidad', 'warning');
        return;
    }
    
    const recipe = appState.data.recipes.find(r => r.id === recipeId);
    if (!recipe) {
        showNotification('Receta no encontrada', 'error');
        return;
    }
    
    showNotification('Calculando ingredientes...', 'info');
    
    // Calculate ingredients needed
    const multiplier = quantity / recipe.yield;
    const projectedQuantity = (quantity / 7) * period; // Project based on period
    
    const calculatedIngredients = recipe.ingredients.map(ingredient => ({
        ...ingredient,
        currentNeeded: ingredient.quantity * multiplier,
        projectedNeeded: ingredient.quantity * (projectedQuantity / recipe.yield),
        unit: ingredient.unit
    }));
    
    // Check inventory for ingredients
    const inventoryCheck = calculatedIngredients.map(ing => {
        const inventoryItem = appState.data.inventory.find(item => 
            item.producto.toLowerCase().includes(ing.name.toLowerCase())
        );
        
        return {
            ...ing,
            currentStock: inventoryItem ? parseInt(inventoryItem.stock_actual) : 0,
            isAvailable: inventoryItem ? (inventoryItem.stock_actual >= ing.currentNeeded) : false,
            needsOrder: inventoryItem ? (inventoryItem.stock_actual < ing.currentNeeded) : true
        };
    });
    
    displayIngredientsCalculation(recipe, quantity, period, inventoryCheck);
    showNotification('Cálculo completado', 'success');
}

function displayIngredientsCalculation(recipe, quantity, period, ingredients) {
    const container = document.getElementById('ingredientsResult');
    
    const totalProjected = ingredients.reduce((sum, ing) => sum + ing.projectedNeeded, 0);
    const unavailableCount = ingredients.filter(ing => !ing.isAvailable).length;
    
    const html = `
        <div class="space-y-4">
            <!-- Summary -->
            <div class="bg-gray-50 rounded-lg p-4">
                <h5 class="font-semibold text-gray-900 mb-2">Resumen del Cálculo</h5>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-600">Receta:</span>
                        <span class="font-medium ml-2">${recipe.name}</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Cantidad actual:</span>
                        <span class="font-medium ml-2">${quantity} ${recipe.unit}</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Proyección (${period} días):</span>
                        <span class="font-medium ml-2">${Math.round(quantity / 7 * period)} ${recipe.unit}</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Ingredientes faltantes:</span>
                        <span class="font-medium ml-2 text-red-600">${unavailableCount}</span>
                    </div>
                </div>
            </div>
            
            <!-- Ingredients Table -->
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Ingrediente</th>
                            <th>Necesario (Actual)</th>
                            <th>Proyectado (${period}d)</th>
                            <th>Stock Actual</th>
                            <th>Estado</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${ingredients.map(ing => `
                            <tr>
                                <td class="font-medium">${ing.name}</td>
                                <td>${ing.currentNeeded.toFixed(1)} ${ing.unit}</td>
                                <td>${ing.projectedNeeded.toFixed(1)} ${ing.unit}</td>
                                <td>${ing.currentStock}</td>
                                <td>
                                    <span class="status-badge status-badge-${ing.isAvailable ? 'success' : 'danger'}">
                                        ${ing.isAvailable ? 'Disponible' : 'Faltante'}
                                    </span>
                                </td>
                                <td>
                                    ${!ing.isAvailable ? `
                                        <button onclick="orderIngredient('${ing.name}', ${ing.currentNeeded - ing.currentStock})" 
                                            class="text-blue-600 hover:text-blue-800 text-sm">
                                            <i class="fas fa-shopping-cart mr-1"></i>Pedir
                                        </button>
                                    ` : '-'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <!-- Actions -->
            <div class="flex space-x-3 pt-4 border-t">
                <button onclick="generatePurchaseOrder(${ingredients.filter(i => !i.isAvailable).length})" 
                    class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm">
                    <i class="fas fa-file-invoice mr-2"></i>Generar Orden de Compra
                </button>
                <button onclick="saveCalculation('${recipe.name}', ${quantity}, ${period})" 
                    class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm">
                    <i class="fas fa-save mr-2"></i>Guardar Cálculo
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function orderIngredient(ingredientName, quantity) {
    showNotification(`Generando pedido para ${ingredientName}: ${quantity.toFixed(1)} unidades`, 'info');
    
    // In a real implementation, this would integrate with a purchasing system
    setTimeout(() => {
        showNotification(`Pedido para ${ingredientName} agregado al carrito`, 'success');
    }, 1000);
}

function generatePurchaseOrder(missingCount) {
    if (missingCount === 0) {
        showNotification('Todos los ingredientes están disponibles', 'info');
        return;
    }
    
    showNotification('Generando orden de compra para ingredientes faltantes...', 'info');
    
    // In a real implementation, this would generate a purchase order
    setTimeout(() => {
        showNotification(`Orden de compra generada para ${missingCount} ingredientes`, 'success');
    }, 1500);
}

function saveCalculation(recipeName, quantity, period) {
    const calculation = {
        recipeName,
        quantity,
        period,
        date: new Date().toISOString(),
        id: Date.now()
    };
    
    // Save to localStorage or send to backend
    let savedCalculations = JSON.parse(localStorage.getItem('recipeCalculations') || '[]');
    savedCalculations.push(calculation);
    localStorage.setItem('recipeCalculations', JSON.stringify(savedCalculations));
    
    showNotification('Cálculo guardado exitosamente', 'success');
}