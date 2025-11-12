import { Recipe, ApiResponse } from './types';
interface RecipeCalculation {
    totalCost: number;
    costPerUnit: number;
    profitMargin: number;
    ingredientCosts: Array<{
        ingredient: string;
        quantity: number;
        unit: string;
        cost: number;
        totalCost: number;
    }>;
}
interface RecipeSuggestion {
    recipe: Recipe;
    score: number;
    reasons: string[];
}
declare class RecipeManager {
    private recipeCache;
    constructor();
    private initializeEventListeners;
    private updateRecipeCosts;
    loadRecipes(): Promise<Recipe[]>;
    addRecipe(recipeData: Omit<Recipe, 'id'>): Promise<ApiResponse<Recipe>>;
    updateRecipe(id: string, updates: Partial<Recipe>): Promise<ApiResponse<Recipe>>;
    deleteRecipe(id: string): Promise<ApiResponse<void>>;
    calculateRecipeCosts(recipe: Omit<Recipe, 'id'>): Promise<RecipeCalculation>;
    private estimateIngredientCost;
    private convertUnits;
    private convertToStandardUnit;
    getRecipeSuggestions(): Promise<RecipeSuggestion[]>;
    private analyzeRecipeFeasibility;
    scaleRecipe(recipeId: string, targetYield: number): Promise<ApiResponse<Recipe>>;
    validateRecipeData(recipe: Omit<Recipe, 'id'>): {
        isValid: boolean;
        errors: string[];
    };
    analyzeMenuPricing(): Promise<{
        recipes: Array<{
            recipe: Recipe;
            currentProfit: number;
            suggestedPrice: number;
            suggestedProfit: number;
            priceRange: {
                min: number;
                max: number;
                optimal: number;
            };
        }>;
        averageProfit: number;
        underpricedRecipes: number;
        overpricedRecipes: number;
    }>;
    private suggestOptimalPrice;
    private calculatePriceRange;
    private roundToAttractivePrice;
    loadRecipesList(): Promise<void>;
    loadRecipeSuggestions(): Promise<void>;
    editRecipe(recipeId: string): void;
    selectRecipe(recipeId: string): void;
}
declare const recipeManager: RecipeManager;
export { RecipeManager, recipeManager };
declare global {
    interface Window {
        recipeManager: RecipeManager;
    }
}
//# sourceMappingURL=recipes.d.ts.map