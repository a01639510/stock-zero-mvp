// Stock Zero - Database Integration JavaScript

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
            const config = await this._loadConfig();

            if (config.supabaseUrl && config.supabaseKey) {
                this.supabaseUrl = config.supabaseUrl;
                this.supabaseKey = config.supabaseKey;
                this.isConnected = true;
                console.log('✅ Connected to Supabase');
                return true;
            } else {
                console.warn('⚠️ No database credentials found, using local storage');
                return false;
            }
        } catch (error) {
            console.error('❌ Database connection failed:', error);
            return false;
        }
    }

    async _loadConfig() {
        // 🔹 Prioridad 1: Variables de entorno (Netlify, Vite, etc.)
        const envUrl = typeof import !== 'undefined' && import.meta?.env?.SUPABASE_URL;
        const envKey = typeof import !== 'undefined' && import.meta?.env?.SUPABASE_KEY;

        if (envUrl && envKey) {
            return {
                supabaseUrl: envUrl,
                supabaseKey: envKey
            };
        }

        // 🔹 Prioridad 2: LocalStorage (modo fallback)
        return {
            supabaseUrl: localStorage.getItem('supabaseUrl') || null,
            supabaseKey: localStorage.getItem('supabaseKey') || null
        };
    }

    async setCredentials(url, key) {
        this.supabaseUrl = url;
        this.supabaseKey = key;

        localStorage.setItem('supabaseUrl', url);
        localStorage.setItem('supabaseKey', key);

        this.isConnected = true;
        showNotification('Credenciales de base de datos guardadas', 'success');
    }

    async testConnection() {
        if (!this.isConnected) {
            const connected = await this.initialize();
            if (!connected) return false;
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/`, {
                headers: {
                    apikey: this.supabaseKey,
                    Authorization: `Bearer ${this.supabaseKey}`
                }
            });

            return response.ok;
        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }

    async fetchSales() {
        return this._fetchData('sales');
    }

    async fetchInventory() {
        return this._fetchData('inventory');
    }

    async fetchRecipes() {
        return this._fetchData('recipes');
    }

    async _fetchData(table) {
        if (!this.isConnected) return this._getLocalData(table);

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/${table}`, {
                headers: {
                    apikey: this.supabaseKey,
                    Authorization: `Bearer ${this.supabaseKey}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this._saveLocalData(table, data);
                return data;
            } else {
                throw new Error(`Failed to fetch ${table}`);
            }
        } catch (error) {
            console.error(`Error fetching ${table}:`, error);
            showNotification(`Error al cargar ${table}, usando caché local`, 'warning');
            return this._getLocalData(table);
        }
    }

    async saveSales(data) {
        return this._saveData('sales', data);
    }

    async saveInventory(data) {
        return this._saveData('inventory', data);
    }

    async _saveData(table, data) {
        if (!this.isConnected) {
            this._saveLocalData(table, data);
            return true;
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/rest/v1/${table}`, {
                method: 'POST',
                headers: {
                    apikey: this.supabaseKey,
                    Authorization: `Bearer ${this.supabaseKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this._saveLocalData(table, data);
                return true;
            } else {
                throw new Error(`Failed to save ${table}`);
            }
        } catch (error) {
            console.error(`Error saving ${table}:`, error);
            showNotification(`Error al guardar ${table}, guardando localmente`, 'warning');
            this._saveLocalData(table, data);
            return false;
        }
    }

    _saveLocalData(type, data) {
        localStorage.setItem(`stockZero_${type}`, JSON.stringify(data));
    }

    _getLocalData(type) {
        const data = localStorage.getItem(`stockZero_${type}`);
        return data ? JSON.parse(data) : [];
    }

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

    async authenticate(email, password) {
        if (!this.isConnected) {
            return { user: { email, name: email.split('@')[0] }, success: true };
        }

        try {
            const response = await fetch(`${this.supabaseUrl}/auth/v1/token?grant_type=password`, {
                method: 'POST',
                headers: {
                    apikey: this.supabaseKey,
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

const dbManager = new DatabaseManager();

async function enhancedSyncData() {
    const isConnected = await dbManager.initialize();
    if (isConnected) {
        return await dbManager.syncAllData();
    } else {
        syncData();
        return false;
    }
}

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
                    <label class="block text-sm font-medium text-gray-700 mb-2">Supabase URL</label>
                    <input type="text" id="dbUrl" placeholder="https://your-project.supabase.co" class="form-input"
                        value="${localStorage.getItem('supabaseUrl') || ''}">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Supabase Anon Key</label>
                    <input type="password" id="dbKey" placeholder="your-anon-key" class="form-input"
                        value="${localStorage.getItem('supabaseKey') || ''}">
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
    if (modal) document.body.removeChild(modal);
}

async function testDatabaseConnection() {
    const url = document.getElementById('dbUrl').value;
    const key = document.getElementById('dbKey').value;
    if (!url || !key) {
        showNotification('Por favor, completa todos los campos', 'warning');
        return;
    }
    showNotification('Probando conexión...', 'info');
    await dbManager.setCredentials(url, key);
    const isConnected = await dbManager.testConnection();
    if (isConnected) showNotification('¡Conexión exitosa!', 'success');
    else showNotification('Error de conexión, verifica tus credenciales', 'error');
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
    setTimeout(() => enhancedSyncData(), 1000);
}

document.addEventListener('DOMContentLoaded', () => {
    dbManager.initialize().then(isConnected => {
        if (isConnected) {
            console.log('Database connected on startup');
            enhancedSyncData();
        } else {
            console.log('Using local storage only');
        }
    });
});
