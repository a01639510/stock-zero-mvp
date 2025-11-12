```javascript
// Connection Test Script - Para diagnosticar problemas de conexión a Supabase

import { createClient } from "@supabase/supabase-js";

class ConnectionTester {
    constructor() {
        this.results = [];
    }

    async testAllMethods() {
        console.log("🔍 Starting comprehensive connection test...");
        
        // Test 1: Environment Variables (VITE_ prefix)
        this.testViteEnvironment();
        
        // Test 2: Environment Variables (no prefix)
        this.testDirectEnvironment();
        
        // Test 3: LocalStorage
        this.testLocalStorage();
        
        // Test 4: Direct connection attempt
        await this.testDirectConnection();
        
        // Test 5: Show summary
        this.showResults();
        
        return this.results;
    }

    testViteEnvironment() {
        const url = typeof import !== "undefined" && import.meta?.env?.VITE_SUPABASE_URL;
        const key = typeof import !== "undefined" && import.meta?.env?.VITE_SUPABASE_KEY;
        
        if (url && key) {
            this.results.push({
                method: "VITE Environment Variables",
                status: "✅ SUCCESS",
                url: url.substring(0, 20) + "...",
                key: key.substring(0, 20) + "..."
            });
        } else {
            this.results.push({
                method: "VITE Environment Variables",
                status: "❌ FAILED",
                url: url ? "Found" : "Not found",
                key: key ? "Found" : "Not found"
            });
        }
    }

    testDirectEnvironment() {
        const url = typeof import !== "undefined" && import.meta?.env?.SUPABASE_URL;
        const key = typeof import !== "undefined" && import.meta?.env?.SUPABASE_KEY;
        
        if (url && key) {
            this.results.push({
                method: "Direct Environment Variables",
                status: "✅ SUCCESS",
                url: url.substring(0, 20) + "...",
                key: key.substring(0, 20) + "..."
            });
        } else {
            this.results.push({
                method: "Direct Environment Variables",
                status: "❌ FAILED",
                url: url ? "Found" : "Not found",
                key: key ? "Found" : "Not found"
            });
        }
    }

    testLocalStorage() {
        const url = localStorage.getItem("supabaseUrl");
        const key = localStorage.getItem("supabaseKey");
        
        if (url && key) {
            this.results.push({
                method: "LocalStorage",
                status: "✅ SUCCESS",
                url: url.substring(0, 20) + "...",
                key: key.substring(0, 20) + "..."
            });
        } else {
            this.results.push({
                method: "LocalStorage",
                status: "❌ FAILED",
                url: url ? "Found" : "Not found",
                key: key ? "Found" : "Not found"
            });
        }
    }

    async testDirectConnection() {
        try {
            // Intentar con VITE_ variables primero
            let url = typeof import !== "undefined" && import.meta?.env?.VITE_SUPABASE_URL;
            let key = typeof import !== "undefined" && import.meta?.env?.VITE_SUPABASE_KEY;
            
            // Si no funcionan, intentar con variables directas
            if (!url || !key) {
                url = typeof import !== "undefined" && import.meta?.env?.SUPABASE_URL;
                key = typeof import !== "undefined" && import.meta?.env?.SUPABASE_KEY;
            }
            
            // Si todavía no funcionan, intentar con localStorage
            if (!url || !key) {
                url = localStorage.getItem("supabaseUrl");
                key = localStorage.getItem("supabaseKey");
            }
            
            if (url && key) {
                const client = createClient(url, key);
                const { data, error } = await client.from('users').select('count').single();
                
                if (error) {
                    this.results.push({
                        method: "Direct Connection Test",
                        status: "❌ FAILED",
                        error: error.message
                    });
                } else {
                    this.results.push({
                        method: "Direct Connection Test",
                        status: "✅ SUCCESS",
                        message: "Successfully connected to Supabase"
                    });
                }
            } else {
                this.results.push({
                    method: "Direct Connection Test",
                    status: "❌ FAILED",
                    error: "No credentials available for testing"
                });
            }
        } catch (error) {
            this.results.push({
                method: "Direct Connection Test",
                status: "❌ FAILED",
                error: error.message
            });
        }
    }

    showResults() {
        console.table(this.results);
        
        const successCount = this.results.filter(r => r.status === "✅ SUCCESS").length;
        const totalCount = this.results.length;
        
        console.log(`📊 Test Summary: ${successCount}/${totalCount} tests passed`);
        
        if (successCount === 0) {
            console.error("🚨 CRITICAL: No connection method worked!");
            console.log("💡 Possible solutions:");
            console.log("1. Check Netlify Environment Variables (should be VITE_SUPABASE_URL and VITE_SUPABASE_KEY)");
            console.log("2. Verify your Supabase project URL and anon key are correct");
            console.log("3. Make sure you redeployed after setting environment variables");
        }
    }

    // Método para configurar credenciales manualmente (fallback)
    setManualCredentials(url, key) {
        localStorage.setItem("supabaseUrl", url);
        localStorage.setItem("supabaseKey", key);
        console.log("✅ Credentials saved to localStorage as fallback");
    }
}

// Exportar para uso en la aplicación
export { ConnectionTester };

// Auto-executar diagnóstico si estamos en desarrollo
if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    window.testConnection = async () => {
        const tester = new ConnectionTester();
        return await tester.testAllMethods();
    };
    
    console.log("🔧 Development mode detected. Run window.testConnection() to diagnose Supabase connection.");
}
```