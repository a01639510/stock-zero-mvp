// Stock Zero - Database Integration JavaScript

// Database Configuration and Connection
class DatabaseManager {
    constructor() {
        this.supabaseUrl = null;
        this.supabaseKey = null;
        this.isConnected = false;
        this.connectionPromise = null;
    }

    async initialize() {
        if (this.connectionPromise) {
            return this.connectionPromise;
        }

        this.connectionPromise = this._connect();
        return this.connectionPromise;
    }

    async _connect() {
        try {
            // Try to get Supabase credentials from environment or config
            const config = await this._loadConfig();
            
            if (config.supabaseUrl && config.supabaseKey) {
                this.supabaseUrl = config.supabaseUrl;
                this.supabaseKey = config.supabaseKey;
                this.isConnected = true;
                console.log('Connected to Supabase database');
                return true;
            } else {
                console.warn('No database credentials found, using local storage');
                return false;
            }
        } catch (error) {
            console.error('Database connection failed:', error);
            return false;
        }
    }

    async _loadConfig() {
        // In a real implementation, this would load from environment variables
        // For now, we'll use a fallback to localStorage
        return {
            supabaseUrl: localStorage.getItem('supabaseUrl') || null,
            supabaseKey: localStorage.getItem('supabaseKey') || null
        };
    }

    async setCredentials(url, key) {
        this.supabaseUrl = url;
        this.supabaseKey = key;
        
        // Store in localStorage for persistence
        localStorage.setItem('supabaseUrl', url);
        localStorage.setItem('supabaseKey', key);
        
        this.isConnected = true;
        showNotification('Credenciales de base de datos guardadas', 'success');
    }

    async testConnection() {
        if (!this.isConnected) {
            const connected = await this.initialize();
            if (!connected) {
                return false;
            }
        }

        try {
            // Test connection with a simple query
            const response = await fetch(`${this.supabaseUrl}/rest/v1/`, {
                headers: {
                    'apikey': this.supabaseKey,
                    'Authorization': `Bearer ${this.supabaseKey}`
                }
            });
            
            return response.ok;
        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }

    // Data Operations
    async fetchSales() {
        if (!this.isConnected) {
            return this._getLocalData('sales');
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/sales`, {
                headers: {
                    'apikey': this.supabaseKey,
                    'Authorization': `Bearer ${this.supabaseKey}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this._saveLocalData('sales', data);
                return data;
            } else {
                throw new Error('Failed to fetch sales data');
            }
        } catch (error) {
            console.error('Error fetching sales:', error);
            showNotification('Error al cargar datos de ventas, usando caché local', 'warning');
            return this._getLocalData('sales');
        }
    }

    async fetchInventory() {
        if (!this.isConnected) {
            return this._getLocalData('inventory');
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/inventory`, {
                headers: {
                    'apikey': this.supabaseKey,
                    'Authorization': `Bearer ${this.supabaseKey}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this._saveLocalData('inventory', data);
                return data;
            } else {
                throw new Error('Failed to fetch inventory data');
            }
        } catch (error) {
            console.error('Error fetching inventory:', error);
            showNotification('Error al cargar datos de inventario, usando caché local', 'warning');
            return this._getLocalData('inventory');
        }
    }

    async fetchRecipes() {
        if (!this.isConnected) {
            return this._getLocalData('recipes');
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/recipes`, {
                headers: {
                    'apikey': this.supabaseKey,
                    'Authorization': `Bearer ${this.supabaseKey}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this._saveLocalData('recipes', data);
                return data;
            } else {
                throw new Error('Failed to fetch recipes data');
            }
        } catch (error) {
            console.error('Error fetching recipes:', error);
            showNotification('Error al cargar recetas, usando caché local', 'warning');
            return this._getLocalData('recipes');
        }
    }

    async saveSales(salesData) {
        if (!this.isConnected) {
            this._saveLocalData('sales', salesData);
            return true;
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/sales`, {
                method: 'POST',
                headers: {
                    'apikey': this.supabaseKey,
                    'Authorization': `Bearer ${this.supabaseKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(salesData)
            });

            if (response.ok) {
                this._saveLocalData('sales', salesData);
                return true;
            } else {
                throw new Error('Failed to save sales data');
            }
        } catch (error) {
            console.error('Error saving sales:', error);
            showNotification('Error al guardar ventas, guardando localmente', 'warning');
            this._saveLocalData('sales', salesData);
            return false;
        }
    }

    async saveInventory(inventoryData) {
        if (!this.isConnected) {
            this._saveLocalData('inventory', inventoryData);
            return true;
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/inventory`, {
                method: 'POST',
                headers: {
                    'apikey': this.supabaseKey,
                    'Authorization': `Bearer ${this.supabaseKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(inventoryData)
            });

            if (response.ok) {
                this._saveLocalData('inventory', inventoryData);
                return true;
            } else {
                throw new Error('Failed to save inventory data');
            }
        } catch (error) {
            console.error('Error saving inventory:', error);
            showNotification('Error al guardar inventario, guardando localmente', 'warning');
            this._saveLocalData('inventory', inventoryData);
            return false;
        }
    }

    // Local Storage Fallbacks
    _saveLocalData(type, data) {
        localStorage.setItem(`stockZero_${type}`, JSON.stringify(data));
    }

    _getLocalData(type) {
        const data = localStorage.getItem(`stockZero_${type}`);
        return data ? JSON.parse(data) : [];
    }

    // Sync Operations
    async syncAllData() {
        showNotification('Sincronizando todos los datos...', 'info');
        
        try {
            const [sales, inventory, recipes] = await Promise.all([
                this.fetchSales(),
                this.fetchInventory(),
                this.fetchRecipes()
            ]);

            appState.data = { sales, inventory, recipes };
            saveData();
            
            showNotification('Datos sincronizados exitosamente', 'success');
            return true;
        } catch (error) {
            console.error('Sync failed:', error);
            showNotification('Error en sincronización', 'error');
            return false;
        }
    }

    // Authentication (if needed)
    async authenticate(email, password) {
        if (!this.isConnected) {
            // Mock authentication for demo
            return { user: { email, name: email.split('@')[0] }, success: true };
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/auth/v1/token?grant_type=password`, {
                method: 'POST',
                headers: {
                    'apikey': this.supabaseKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                const data = await response.json();
                return { user: data.user, success: true };
            } else {
                return { success: false, error: 'Invalid credentials' };
            }
        } catch (error) {
            console.error('Authentication failed:', error);
            return { success: false, error: error.message };
        }
    }
}

// Global database manager instance
const dbManager = new DatabaseManager();

// Enhanced sync function that uses the database manager
async function enhancedSyncData() {
    const isConnected = await dbManager.initialize();
    
    if (isConnected) {
        return await dbManager.syncAllData();
    } else {
        // Fallback to basic sync
        syncData();
        return false;
    }
}

// Database configuration modal
function showDatabaseConfig() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-database text-blue-600 mr-2"></i>Configurar Base de Datos
            </h3>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Supabase URL
                    </label>
                    <input type="text" id="dbUrl" placeholder="https://your-project.supabase.co" 
                           class="form-input" value="${localStorage.getItem('supabaseUrl') || ''}">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Supabase Anon Key
                    </label>
                    <input type="password" id="dbKey" placeholder="your-anon-key" 
                           class="form-input" value="${localStorage.getItem('supabaseKey') || ''}">
                </div>
                
                <div class="text-xs text-gray-500">
                    <p>Obtén estas credenciales desde tu proyecto de Supabase:</p>
                    <p>1. Ve a Settings → API</p>
                    <p>2. Copia la URL y la anon key</p>
                </div>
            </div>
            
            <div class="flex space-x-3 mt-6">
                <button onclick="closeDatabaseConfig()" class="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300">
                    Cancelar
                </button>
                <button onclick="testDatabaseConnection()" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                    Probar Conexión
                </button>
                <button onclick="saveDatabaseConfig()" class="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
                    Guardar
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function closeDatabaseConfig() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        document.body.removeChild(modal);
    }
}

async function testDatabaseConnection() {
    const url = document.getElementById('dbUrl').value;
    const key = document.getElementById('dbKey').value;
    
    if (!url || !key) {
        showNotification('Por favor, completa todos los campos', 'warning');
        return;
    }
    
    showNotification('Probando conexión...', 'info');
    
    // Temporarily set credentials for testing
    await dbManager.setCredentials(url, key);
    const isConnected = await dbManager.testConnection();
    
    if (isConnected) {
        showNotification('¡Conexión exitosa!', 'success');
    } else {
        showNotification('Error de conexión, verifica tus credenciales', 'error');
    }
}

async function saveDatabaseConfig() {
    const url = document.getElementById('dbUrl').value;
    const key = document.getElementById('dbKey').value;
    
    if (!url || !key) {
        showNotification('Por favor, completa todos los campos', 'warning');
        return;
    }
    
    await dbManager.setCredentials(url, key);
    closeDatabaseConfig();
    
    // Try to sync data with new configuration
    setTimeout(() => {
        enhancedSyncData();
    }, 1000);
}

// Initialize database on app load
document.addEventListener('DOMContentLoaded', function() {
    // Try to initialize database connection
    dbManager.initialize().then(isConnected => {
        if (isConnected) {
            console.log('Database connected on startup');
            // Try to sync data
            enhancedSyncData();
        } else {
            console.log('Using local storage only');
        }
    });
});