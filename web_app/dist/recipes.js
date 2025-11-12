import { dataManager } from './data-management';
class RecipeManager {
    constructor() {
        this.recipeCache = new Map();
        this.initializeEventListeners();
    }
    initializeEventListeners() {
        document.addEventListener('inventoryUpdated', () => this.updateRecipeCosts());
    }
    async updateRecipeCosts() {
        for (const [id, recipe] of this.recipeCache) {
            const calculation = await this.calculateRecipeCosts(recipe);
            await this.updateRecipe(id, {
                costPerUnit: calculation.costPerUnit,
                profitMargin: calculation.profitMargin
            });
        }
    }
    async loadRecipes() {
        try {
            const recipes = await dataManager.loadRecipes();
            recipes.forEach(recipe => {
                this.recipeCache.set(recipe.id, recipe);
            });
            return recipes;
        }
        catch (error) {
            console.error('Error loading recipes:', error);
            return [];
        }
    }
    async addRecipe(recipeData) {
        try {
            const validation = this.validateRecipeData(recipeData);
            if (!validation.isValid) {
                return {
                    success: false,
                    error: `Validation errors: ${validation.errors.join(', ')}`
                };
            }
            const calculation = await this.calculateRecipeCosts(recipeData);
            const recipe = {
                ...recipeData,
                costPerUnit: calculation.costPerUnit,
                profitMargin: calculation.profitMargin
            };
            const response = await dataManager.addRecipe(recipe);
            if (response.success && response.data) {
                this.recipeCache.set(response.data.id, response.data);
            }
            return response;
        }
        catch (error) {
            console.error('Error adding recipe:', error);
            return { success: false, error: error.message };
        }
    }
    async updateRecipe(id, updates) {
        try {
            if (updates.ingredients || updates.sellingPrice) {
                const currentRecipe = this.recipeCache.get(id);
                if (currentRecipe) {
                    const updatedRecipe = { ...currentRecipe, ...updates };
                    const calculation = await this.calculateRecipeCosts(updatedRecipe);
                    updates.costPerUnit = calculation.costPerUnit;
                    updates.profitMargin = calculation.profitMargin;
                }
            }
            const response = await dataManager.updateRecipe(id, updates);
            if (response.success && response.data) {
                this.recipeCache.set(id, response.data);
            }
            return response;
        }
        catch (error) {
            console.error('Error updating recipe:', error);
            return { success: false, error: error.message };
        }
    }
    async deleteRecipe(id) {
        try {
            const response = await dataManager.deleteRecipe(id);
            if (response.success) {
                this.recipeCache.delete(id);
            }
            return response;
        }
        catch (error) {
            console.error('Error deleting recipe:', error);
            return { success: false, error: error.message };
        }
    }
    async calculateRecipeCosts(recipe) {
        try {
            const inventory = await dataManager.loadInventory();
            const ingredientCosts = [];
            let totalCost = 0;
            for (const ingredient of recipe.ingredients) {
                const inventoryItem = inventory.find(item => item.name.toLowerCase().includes(ingredient.name.toLowerCase()));
                let ingredientCost = 0;
                if (inventoryItem) {
                    const unitConversion = this.convertUnits(ingredient.quantity, ingredient.unit, inventoryItem.unit);
                    ingredientCost = (unitConversion / parseFloat(inventoryItem.unit)) * inventoryItem.cost;
                }
                else {
                    ingredientCost = await this.estimateIngredientCost(ingredient.name, ingredient.quantity, ingredient.unit);
                }
                const totalIngredientCost = ingredientCost;
                totalCost += totalIngredientCost;
                ingredientCosts.push({
                    ingredient: ingredient.name,
                    quantity: ingredient.quantity,
                    unit: ingredient.unit,
                    cost: ingredientCost,
                    totalCost: totalIngredientCost
                });
            }
            const costPerUnit = totalCost / recipe.yield;
            const profitMargin = ((recipe.sellingPrice - costPerUnit) / recipe.sellingPrice) * 100;
            return {
                totalCost,
                costPerUnit,
                profitMargin,
                ingredientCosts
            };
        }
        catch (error) {
            console.error('Error calculating recipe costs:', error);
            return {
                totalCost: 0,
                costPerUnit: 0,
                profitMargin: 0,
                ingredientCosts: []
            };
        }
    }
    async estimateIngredientCost(name, quantity, unit) {
        const marketPrices = {
            'harina': 2.5,
            'azúcar': 3.0,
            'huevo': 0.2,
            'leche': 1.5,
            'mantequilla': 8.0,
            'sal': 1.0,
            'levadura': 15.0,
            'vainilla': 20.0,
            'chocolate': 12.0,
            'fruta': 5.0,
            'nuez': 25.0,
            'canela': 8.0,
            'aceite': 4.0,
            'agua': 0.001
        };
        const normalizedName = name.toLowerCase();
        const basePrice = marketPrices[normalizedName] || 5.0;
        const standardQuantity = this.convertToStandardUnit(quantity, unit);
        return basePrice * standardQuantity;
    }
    convertUnits(quantity, fromUnit, toUnit) {
        const conversions = {
            'g': 0.001,
            'kg': 1,
            'mg': 0.000001,
            'lb': 0.453592,
            'oz': 0.0283495,
            'ml': 0.001,
            'l': 1,
            'tsp': 0.005,
            'tbsp': 0.015,
            'cup': 0.24,
            'unidad': 1,
            'pieza': 1
        };
        const fromFactor = conversions[fromUnit.toLowerCase()] || 1;
        const toFactor = conversions[toUnit.toLowerCase()] || 1;
        return (quantity * fromFactor) / toFactor;
    }
    convertToStandardUnit(quantity, unit) {
        return this.convertUnits(quantity, unit, 'kg');
    }
    async getRecipeSuggestions() {
        try {
            const [recipes, inventory] = await Promise.all([
                this.loadRecipes(),
                dataManager.loadInventory()
            ]);
            const suggestions = [];
            for (const recipe of recipes) {
                const analysis = this.analyzeRecipeFeasibility(recipe, inventory);
                if (analysis.score > 0) {
                    suggestions.push({
                        recipe,
                        score: analysis.score,
                        reasons: analysis.reasons
                    });
                }
            }
            suggestions.sort((a, b) => b.score - a.score);
            return suggestions.slice(0, 5);
        }
        catch (error) {
            console.error('Error generating recipe suggestions:', error);
            return [];
        }
    }
    analyzeRecipeFeasibility(recipe, inventory) {
        let score = 0;
        const reasons = [];
        let availableIngredients = 0;
        let totalIngredients = recipe.ingredients.length;
        for (const ingredient of recipe.ingredients) {
            const inventoryItem = inventory.find(item => item.name.toLowerCase().includes(ingredient.name.toLowerCase()));
            if (inventoryItem) {
                const unitConversion = this.convertUnits(ingredient.quantity, ingredient.unit, inventoryItem.unit);
                if (inventoryItem.quantity >= unitConversion) {
                    availableIngredients++;
                    score += 20;
                }
                else {
                    score += 5;
                    reasons.push(`Falta ${ingredient.name} (${unitConversion - inventoryItem.quantity} ${inventoryItem.unit})`);
                }
            }
            else {
                reasons.push(`No hay ${ingredient.name} en inventario`);
            }
        }
        if (recipe.profitMargin > 50) {
            score += 10;
            reasons.push('Alta rentabilidad');
        }
        if (availableIngredients === totalIngredients) {
            score += 30;
            reasons.unshift('Todos los ingredientes disponibles');
        }
        return { score, reasons };
    }
    async scaleRecipe(recipeId, targetYield) {
        try {
            const recipe = this.recipeCache.get(recipeId);
            if (!recipe) {
                return { success: false, error: 'Receta no encontrada' };
            }
            const scaleFactor = targetYield / recipe.yield;
            const scaledIngredients = recipe.ingredients.map(ingredient => ({
                ...ingredient,
                quantity: ingredient.quantity * scaleFactor
            }));
            const updates = {
                ingredients: scaledIngredients,
                yield: targetYield
            };
            const calculation = await this.calculateRecipeCosts({ ...recipe, ...updates });
            updates.costPerUnit = calculation.costPerUnit;
            updates.profitMargin = calculation.profitMargin;
            return await this.updateRecipe(recipeId, updates);
        }
        catch (error) {
            console.error('Error scaling recipe:', error);
            return { success: false, error: error.message };
        }
    }
    validateRecipeData(recipe) {
        const errors = [];
        if (!recipe.name || recipe.name.trim().length === 0) {
            errors.push('El nombre de la receta es requerido');
        }
        if (!recipe.ingredients || recipe.ingredients.length === 0) {
            errors.push('La receta debe tener al menos un ingrediente');
        }
        if (recipe.yield <= 0) {
            errors.push('El rendimiento debe ser mayor a 0');
        }
        if (recipe.sellingPrice <= 0) {
            errors.push('El precio de venta debe ser mayor a 0');
        }
        recipe.ingredients.forEach((ingredient, index) => {
            if (!ingredient.name || ingredient.name.trim().length === 0) {
                errors.push(`Ingrediente ${index + 1}: nombre requerido`);
            }
            if (ingredient.quantity <= 0) {
                errors.push(`Ingrediente ${index + 1}: cantidad debe ser mayor a 0`);
            }
            if (!ingredient.unit || ingredient.unit.trim().length === 0) {
                errors.push(`Ingrediente ${index + 1}: unidad requerida`);
            }
        });
        return {
            isValid: errors.length === 0,
            errors
        };
    }
    async analyzeMenuPricing() {
        try {
            const recipes = await this.loadRecipes();
            const analysis = [];
            let totalProfit = 0;
            let underpricedCount = 0;
            let overpricedCount = 0;
            for (const recipe of recipes) {
                const costAnalysis = await this.calculateRecipeCosts(recipe);
                const currentProfit = recipe.profitMargin;
                const costPerUnit = costAnalysis.costPerUnit;
                const suggestedPrice = this.suggestOptimalPrice(costPerUnit);
                const suggestedProfit = ((suggestedPrice - costPerUnit) / suggestedPrice) * 100;
                const priceRange = this.calculatePriceRange(costPerUnit);
                analysis.push({
                    recipe,
                    currentProfit,
                    suggestedPrice,
                    suggestedProfit,
                    priceRange
                });
                totalProfit += currentProfit;
                if (currentProfit < 30)
                    underpricedCount++;
                if (currentProfit > 70)
                    overpricedCount++;
            }
            const averageProfit = totalProfit / recipes.length;
            return {
                recipes: analysis,
                averageProfit,
                underpricedRecipes: underpricedCount,
                overpricedRecipes: overpricedCount
            };
        }
        catch (error) {
            console.error('Error analyzing menu pricing:', error);
            return {
                recipes: [],
                averageProfit: 0,
                underpricedRecipes: 0,
                overpricedRecipes: 0
            };
        }
    }
    suggestOptimalPrice(costPerUnit) {
        const baseMargin = 0.5;
        const suggestedPrice = costPerUnit / (1 - baseMargin);
        return this.roundToAttractivePrice(suggestedPrice);
    }
    calculatePriceRange(costPerUnit) {
        const minMargin = 0.3;
        const maxMargin = 0.7;
        const optimalMargin = 0.5;
        return {
            min: costPerUnit / (1 - minMargin),
            max: costPerUnit / (1 - maxMargin),
            optimal: costPerUnit / (1 - optimalMargin)
        };
    }
    roundToAttractivePrice(price) {
        const rounded = Math.ceil(price);
        if (rounded - price < 0.5) {
            return rounded - 0.01;
        }
        else {
            return rounded - 0.5;
        }
    }
    async loadRecipesList() {
        try {
            const recipes = await this.loadRecipes();
            const recipesListElement = document.getElementById('recipesList');
            if (recipesListElement) {
                recipesListElement.innerHTML = `
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        ${recipes.map(recipe => `
                            <div class="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
                                <div class="flex justify-between items-start mb-2">
                                    <h3 class="font-semibold text-gray-800">${recipe.name}</h3>
                                    <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                                        ${recipe.category}
                                    </span>
                                </div>
                                <div class="space-y-1 text-sm text-gray-600">
                                    <p>Rendimiento: ${recipe.yield} unidades</p>
                                    <p>Costo por unidad: $${recipe.costPerUnit.toFixed(2)}</p>
                                    <p>Precio de venta: $${recipe.sellingPrice.toFixed(2)}</p>
                                    <p>Margen de ganancia: ${recipe.profitMargin.toFixed(1)}%</p>
                                </div>
                                <div class="mt-3 flex space-x-2">
                                    <button onclick="recipeManager.editRecipe('${recipe.id}')" 
                                            class="flex-1 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                                        Editar
                                    </button>
                                    <button onclick="recipeManager.deleteRecipe('${recipe.id}')" 
                                            class="flex-1 bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700">
                                        Eliminar
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            await this.loadRecipeSuggestions();
        }
        catch (error) {
            console.error('Error loading recipes list:', error);
        }
    }
    async loadRecipeSuggestions() {
        try {
            const suggestions = await this.getRecipeSuggestions();
            const suggestionsElement = document.getElementById('recipeSuggestions');
            if (suggestionsElement) {
                if (suggestions.length > 0) {
                    suggestionsElement.innerHTML = `
                        <div class="bg-white rounded-lg shadow p-4">
                            <h3 class="text-lg font-semibold text-gray-800 mb-3">Recetas Recomendadas</h3>
                            <div class="space-y-3">
                                ${suggestions.map(suggestion => `
                                    <div class="border rounded-lg p-3 hover:bg-gray-50 cursor-pointer"
                                         onclick="recipeManager.selectRecipe('${suggestion.recipe.id}')">
                                        <div class="flex justify-between items-start">
                                            <div>
                                                <h4 class="font-medium text-gray-800">${suggestion.recipe.name}</h4>
                                                <p class="text-sm text-gray-600">
                                                    Margen: ${suggestion.recipe.profitMargin.toFixed(1)}%
                                                </p>
                                            </div>
                                            <span class="text-sm font-medium text-green-600">
                                                ${suggestion.score.toFixed(0)}% coincidencia
                                            </span>
                                        </div>
                                        <div class="mt-2">
                                            <p class="text-xs text-gray-500">
                                                ${suggestion.reasons.join(', ')}
                                            </p>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
                else {
                    suggestionsElement.innerHTML = `
                        <div class="bg-white rounded-lg shadow p-4">
                            <h3 class="text-lg font-semibold text-gray-800 mb-3">Recetas Recomendadas</h3>
                            <p class="text-gray-600">No hay recetas que puedan prepararse con los ingredientes actuales.</p>
                        </div>
                    `;
                }
            }
        }
        catch (error) {
            console.error('Error loading recipe suggestions:', error);
        }
    }
    editRecipe(recipeId) {
        const recipe = this.recipeCache.get(recipeId);
        if (recipe) {
            const editForm = document.getElementById('recipeEditForm');
            if (editForm) {
                editForm.elements.namedItem('recipeName').value = recipe.name;
                editForm.elements.namedItem('recipeCategory').value = recipe.category;
                editForm.elements.namedItem('recipeYield').value = recipe.yield.toString();
                editForm.elements.namedItem('recipePrice').value = recipe.sellingPrice.toString();
                const editModal = document.getElementById('recipeEditModal');
                if (editModal) {
                    editModal.classList.remove('hidden');
                }
            }
        }
    }
    selectRecipe(recipeId) {
        const recipe = this.recipeCache.get(recipeId);
        if (recipe) {
            const detailsElement = document.getElementById('recipeDetails');
            if (detailsElement) {
                detailsElement.innerHTML = `
                    <div class="bg-white rounded-lg shadow p-6">
                        <h2 class="text-xl font-bold text-gray-800 mb-4">${recipe.name}</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 class="font-semibold text-gray-700 mb-2">Ingredientes</h3>
                                <ul class="space-y-1">
                                    ${recipe.ingredients.map(ing => `
                                        <li class="text-sm text-gray-600">
                                            ${ing.quantity} ${ing.unit} de ${ing.name}
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-700 mb-2">Información Financiera</h3>
                                <div class="space-y-1 text-sm text-gray-600">
                                    <p>Costo por unidad: $${recipe.costPerUnit.toFixed(2)}</p>
                                    <p>Precio de venta: $${recipe.sellingPrice.toFixed(2)}</p>
                                    <p>Margen de ganancia: ${recipe.profitMargin.toFixed(1)}%</p>
                                    <p>Rendimiento: ${recipe.yield} unidades</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }
}
const recipeManager = new RecipeManager();
export { RecipeManager, recipeManager };
window.recipeManager = recipeManager;
//# sourceMappingURL=recipes.js.map