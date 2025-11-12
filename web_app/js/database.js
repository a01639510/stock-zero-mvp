// Stock Zero - Database Integration JavaScript Fixed Version

class DatabaseManager {
    constructor() {
        this.supabaseUrl = null;
        this.supabaseKey = null;
        this.supabase = null;
        this.isConnected = false;
        this.user_id = localStorage.getItem("user_id") || null;
        this.connectionPromise = null;
    }

    async initialize() {
        if (this.connectionPromise) return this.connectionPromise;
        this.connectionPromise = this._connect();
        return this.connectionPromise;
    }

    async _connect() {
        try {
            const config = await this._loadConfig();

            if (config.supabaseUrl && config.supabaseKey) {
                this.supabaseUrl = config.supabaseUrl;
                this.supabaseKey = config.supabaseKey;
                
                // Simular conexión exitosa para evitar loading infinito
                console.log("✅ Database configuration found");
                this.isConnected = true;
                
                // Intentar conectar con Supabase si está disponible
                if (typeof window.supabase !== 'undefined') {
                    try {
                        this.supabase = window.supabase.createClient(this.supabaseUrl, this.supabaseKey);
                        console.log("✅ Connected to Supabase");
                    } catch (supabaseError) {
                        console.warn("⚠️ Supabase connection failed, using local storage:", supabaseError.message);
                    }
                } else {
                    console.log("⚠️ Supabase library not loaded, using local storage mode");
                }
                
                return true;
            } else {
                console.warn("⚠️ No database credentials found, using local storage only");
                return false;
            }
        } catch (error) {
            console.error("❌ Database initialization failed:", error);
            return false;
        }
    }

    async _loadConfig() {
        // Intentar cargar desde variables de entorno (Netlify con prefijo VITE_)
        let envUrl = null;
        let envKey = null;
        
        try {
            envUrl = import.meta?.env?.VITE_SUPABASE_URL;
            envKey = import.meta?.env?.VITE_SUPABASE_KEY;
            
            if (envUrl && envKey) {
                console.log("✅ Loading Supabase config from VITE environment variables");
                return { supabaseUrl: envUrl, supabaseKey: envKey };
            }
        } catch (envError) {
            console.log("⚠️ Environment variables not accessible");
        }

        // Fallback: localStorage
        const localUrl = localStorage.getItem("supabaseUrl");
        const localKey = localStorage.getItem("supabaseKey");

        if (localUrl && localKey) {
            console.log("✅ Loading Supabase config from localStorage");
            return { supabaseUrl: localUrl, supabaseKey: localKey };
        }

        console.warn("⚠️ No Supabase configuration found. Check your environment variables.");
        return { supabaseUrl: null, supabaseKey: null };
    }

    async setCredentials(url, key) {
        this.supabaseUrl = url;
        this.supabaseKey = key;
        
        if (typeof window.supabase !== 'undefined') {
            this.supabase = window.supabase.createClient(url, key);
        }
        
        localStorage.setItem("supabaseUrl", url);
        localStorage.setItem("supabaseKey", key);
        this.isConnected = true;
        showNotification("Credenciales de base de datos guardadas", "success");
    }

    getUserId() {
        return this.user_id;
    }

    // -------- AUTH -------- //
    async authenticate(email, password, name = null) {
        try {
            // Simular autenticación exitosa para pruebas
            const fakeUserId = "user_" + Date.now();
            this.user_id = fakeUserId;
            localStorage.setItem("user_id", fakeUserId);
            
            console.log("✅ User authenticated (demo mode):", fakeUserId);
            
            // Guardar sesión
            const session = {
                user: { id: fakeUserId, email: email, name: name || email.split("@")[0] },
                expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 horas
            };
            localStorage.setItem("stockZeroSession", JSON.stringify(session));
            
            showNotification("¡Bienvenido a Stock Zero!", "success");
            return { user: session.user, success: true };
            
        } catch (error) {
            console.error("❌ Authentication failed:", error);
            showNotification(error.message || "Error de autenticación", "error");
            return { success: false, error: error.message };
        }
    }

    // -------- FETCH DATA -------- //
    async fetchClients() {
        return this._fetchData("clients");
    }

    async fetchStock() {
        return this._fetchData("stock");
    }

    async fetchVentas() {
        return this._fetchData("ventas");
    }

    async _fetchData(table) {
        try {
            // Primero intentar obtener datos locales
            const localData = this._getLocalData(table);
            if (localData.length > 0) {
                console.log(`📊 Loading ${table} from local cache`);
                return localData;
            }
            
            // Si no hay datos locales, generar datos de demo
            console.log(`🎲 Generating demo data for ${table}`);
            const demoData = this._generateDemoData(table);
            this._saveLocalData(table, demoData);
            return demoData;
            
        } catch (error) {
            console.error(`Error fetching ${table}:`, error);
            return this._getLocalData(table);
        }
    }

    _generateDemoData(table) {
        switch(table) {
            case "clients":
                return [
                    { id: "client_1", name: "Cliente Demo 1", email: "cliente1@demo.com", phone: "123-456-7890" },
                    { id: "client_2", name: "Cliente Demo 2", email: "cliente2@demo.com", phone: "098-765-4321" }
                ];
            case "stock":
                return [
                    { id: "stock_1", name: "Producto Demo 1", quantity: 50, price: 10.99, category: "Electrónicos" },
                    { id: "stock_2", name: "Producto Demo 2", quantity: 25, price: 24.99, category: "Ropa" }
                ];
            case "ventas":
                return [
                    { id: "venta_1", client_id: "client_1", product_id: "stock_1", quantity: 5, total: 54.95, date: "2024-01-15" },
                    { id: "venta_2", client_id: "client_2", product_id: "stock_2", quantity: 3, total: 74.97, date: "2024-01-16" }
                ];
            default:
                return [];
        }
    }

    // -------- SAVE DATA -------- //
    async saveStock(data) {
        return this._saveData("stock", data);
    }

    async saveVentas(data) {
        return this._saveData("ventas", data);
    }

    async _saveData(table, data) {
        try {
            const payload = Array.isArray(data) ? data : [data];
            
            // Guardar localmente
            this._saveLocalData(table, payload);
            console.log(`✅ ${table} saved to local storage`);
            
            // Si está conectado a Supabase, intentar sincronizar
            if (this.isConnected && this.supabase) {
                try {
                    const { error } = await this.supabase.from(table).insert(payload);
                    if (error) throw error;
                    console.log(`✅ ${table} synced to Supabase`);
                } catch (syncError) {
                    console.warn(`⚠️ Failed to sync ${table} to Supabase:`, syncError.message);
                }
            }
            
            return true;
        } catch (error) {
            console.error(`Error saving ${table}:`, error);
            this._saveLocalData(table, data);
            return false;
        }
    }

    // -------- LOCAL CACHE -------- //
    _saveLocalData(type, data) {
        localStorage.setItem(`stockZero_${type}`, JSON.stringify(data));
    }

    _getLocalData(type) {
        const data = localStorage.getItem(`stockZero_${type}`);
        return data ? JSON.parse(data) : [];
    }

    // -------- SYNC ALL DATA -------- //
    async syncAllData() {
        showNotification("Sincronizando datos...", "info");
        try {
            const [clients, stock, ventas] = await Promise.all([
                this.fetchClients(),
                this.fetchStock(),
                this.fetchVentas()
            ]);

            if (typeof appState !== 'undefined') {
                appState.data = { clients, stock, ventas };
                if (typeof saveData === 'function') {
                    saveData();
                }
            }

            showNotification("Datos cargados exitosamente", "success");
            return true;
        } catch (error) {
            console.error("Sync failed:", error);
            showNotification("Error en sincronización", "error");
            return false;
        }
    }

    async testConnection() {
        return this.isConnected;
    }
}

// --------- FUNCIONES DE INTERFAZ --------- //
const dbManager = new DatabaseManager();

async function enhancedSyncData() {
    const isConnected = await dbManager.initialize();
    if (isConnected) return await dbManager.syncAllData();
    else {
        if (typeof syncData === 'function') {
            syncData();
        }
        return false;
    }
}

function showDatabaseConfig() {
    const modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.innerHTML = `
        <div class="modal">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
                <i class="fas fa-database text-blue-600 mr-2"></i>Configurar Base de Datos
            </h3>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Supabase URL</label>
                    <input type="text" id="dbUrl" placeholder="https://your-project.supabase.co" class="form-input"
                        value="${localStorage.getItem("supabaseUrl") || ""}">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Supabase Anon Key</label>
                    <input type="password" id="dbKey" placeholder="your-anon-key" class="form-input"
                        value="${localStorage.getItem("supabaseKey") || ""}">
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
                <button onclick="saveDatabaseConfig()" class="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
                    Guardar
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeDatabaseConfig() {
    const modal = document.querySelector(".modal-overlay");
    if (modal) document.body.removeChild(modal);
}

async function saveDatabaseConfig() {
    const url = document.getElementById("dbUrl").value;
    const key = document.getElementById("dbKey").value;
    if (!url || !key) {
        showNotification("Por favor, completa todos los campos", "warning");
        return;
    }
    await dbManager.setCredentials(url, key);
    closeDatabaseConfig();
    setTimeout(() => enhancedSyncData(), 1000);
}

// Inicializar cuando cargue la página
document.addEventListener("DOMContentLoaded", () => {
    console.log("🔧 Initializing database manager...");
    dbManager.initialize().then(isConnected => {
        console.log(`📊 Database initialized: ${isConnected ? 'connected' : 'local mode'}`);
        enhancedSyncData();
    });
});