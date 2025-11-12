// Stock Zero - Database Integration JavaScript (versión completa y adaptada a tus tablas reales)
import { createClient } from "@supabase/supabase-js";

class DatabaseManager {
    constructor() {
        this.supabaseUrl = null;
        this.supabaseKey = null;
        this.supabase = null;
        this.isConnected = false;
        this.user_id = localStorage.getItem('user_id') || null;
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
                this.supabase = createClient(this.supabaseUrl, this.supabaseKey);
                this.isConnected = true;
                console.log("✅ Connected to Supabase");
                return true;
            } else {
                console.warn("⚠️ No database credentials found, using local storage");
                return false;
            }
        } catch (error) {
            console.error("❌ Database connection failed:", error);
            return false;
        }
    }

    async _loadConfig() {
        const envUrl = typeof import !== "undefined" && import.meta?.env?.SUPABASE_URL;
        const envKey = typeof import !== "undefined" && import.meta?.env?.SUPABASE_KEY;

        if (envUrl && envKey) {
            return { supabaseUrl: envUrl, supabaseKey: envKey };
        }

        return {
            supabaseUrl: localStorage.getItem("supabaseUrl") || null,
            supabaseKey: localStorage.getItem("supabaseKey") || null,
        };
    }

    async setCredentials(url, key) {
        this.supabaseUrl = url;
        this.supabaseKey = key;
        this.supabase = createClient(url, key);
        localStorage.setItem("supabaseUrl", url);
        localStorage.setItem("supabaseKey", key);
        this.isConnected = true;
        showNotification("Credenciales de base de datos guardadas", "success");
    }

    async authenticate(email, password) {
        if (!this.isConnected) await this.initialize();
        try {
            const { data, error } = await this.supabase.auth.signInWithPassword({ email, password });
            if (error) throw error;
            this.user_id = data.user.id;
            localStorage.setItem("user_id", this.user_id);
            console.log("🔐 Usuario autenticado:", this.user_id);
            return { user: data.user, success: true };
        } catch (error) {
            console.error("Authentication failed:", error);
            return { success: false, error: error.message };
        }
    }

    getUserId() {
        return this.user_id;
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
        if (!this.isConnected) return this._getLocalData(table);
        if (!this.user_id && table !== "clients") {
            console.warn("⚠️ No user_id available for filtering data.");
            return [];
        }

        try {
            let query = this.supabase.from(table).select("*");
            if (table !== "clients") query = query.eq("user_id", this.user_id);

            const { data, error } = await query;
            if (error) throw error;

            this._saveLocalData(table, data);
            return data;
        } catch (error) {
            console.error(`Error fetching ${table}:`, error);
            showNotification(`Error al cargar ${table}, usando caché local`, "warning");
            return this._getLocalData(table);
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
        if (!this.user_id) {
            console.error("❌ No user_id - cannot save data");
            return false;
        }

        const payload = Array.isArray(data)
            ? data.map(d => ({ ...d, user_id: this.user_id }))
            : { ...data, user_id: this.user_id };

        if (!this.isConnected) {
            this._saveLocalData(table, payload);
            return true;
        }

        try {
            const { error } = await this.supabase.from(table).insert(payload);
            if (error) throw error;
            this._saveLocalData(table, payload);
            console.log(`✅ ${table} saved successfully`);
            return true;
        } catch (error) {
            console.error(`Error saving ${table}:`, error);
            showNotification(`Error al guardar ${table}, guardando localmente`, "warning");
            this._saveLocalData(table, payload);
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
        showNotification("Sincronizando todos los datos...", "info");
        try {
            const [clients, stock, ventas] = await Promise.all([
                this.fetchClients(),
                this.fetchStock(),
                this.fetchVentas()
            ]);

            appState.data = { clients, stock, ventas };
            saveData();

            showNotification("Datos sincronizados exitosamente", "success");
            return true;
        } catch (error) {
            console.error("Sync failed:", error);
            showNotification("Error en sincronización", "error");
            return false;
        }
    }

    async testConnection() {
        if (!this.isConnected) await this.initialize();
        try {
            const { error } = await this.supabase.from("clients").select("id").limit(1);
            if (error) throw error;
            return true;
        } catch (error) {
            console.error("Connection test failed:", error);
            return false;
        }
    }
}

// --------- FUNCIONES DE INTERFAZ --------- //
const dbManager = new DatabaseManager();

async function enhancedSyncData() {
    const isConnected = await dbManager.initialize();
    if (isConnected) return await dbManager.syncAllData();
    else {
        syncData();
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
    const modal = document.querySelector(".modal-overlay");
    if (modal) document.body.removeChild(modal);
}

async function testDatabaseConnection() {
    const url = document.getElementById("dbUrl").value;
    const key = document.getElementById("dbKey").value;
    if (!url || !key) {
        showNotification("Por favor, completa todos los campos", "warning");
        return;
    }
    showNotification("Probando conexión...", "info");
    await dbManager.setCredentials(url, key);
    const isConnected = await dbManager.testConnection();
    if (isConnected) showNotification("¡Conexión exitosa!", "success");
    else showNotification("Error de conexión, verifica tus credenciales", "error");
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

document.addEventListener("DOMContentLoaded", () => {
    dbManager.initialize().then(isConnected => {
        if (isConnected) {
            console.log("Database connected on startup");
            enhancedSyncData();
        } else {
            console.log("Using local storage only");
        }
    });
});
