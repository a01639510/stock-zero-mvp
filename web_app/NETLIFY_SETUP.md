```markdown
# 🚀 Configuración de Supabase en Netlify - Guía Completa

## 📋 Problema Identificado
Tu aplicación está funcionando en Netlify pero **no está conectada a Supabase**. Los datos no se guardan, la autenticación no funciona y los análisis están vacíos.

## 🔧 Solución Paso a Paso

### 1️⃣ Obtén tus credenciales de Supabase

1. Ve a tu dashboard de Supabase: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a **Settings** > **API**
4. Copia estos dos valores:
   - **Project URL** (ej: `https://xxxxxxxx.supabase.co`)
   - **anon public** key (la que comienza con `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

### 2️⃣ Configura las variables de entorno en Netlify

1. Ve a tu dashboard de Netlify
2. Selecciona tu sitio (site)
3. Ve a **Site settings** > **Environment variables**
4. Agrega estas dos variables:

```
Variable Name: VITE_SUPABASE_URL
Value: https://xxxxxxxx.supabase.co

Variable Name: VITE_SUPABASE_KEY  
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**⚠️ IMPORTANTE**: Usa el prefijo `VITE_` para que las variables funcionen en Vite/Netlify.

### 3️⃣ Configura las tablas en Supabase

Ejecuta este SQL en tu dashboard de Supabase > **SQL Editor**:

```sql
-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de datos de ventas
CREATE TABLE IF NOT EXISTS sales_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    fecha DATE NOT NULL,
    producto VARCHAR(255) NOT NULL,
    cantidad_vendida DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de inventario
CREATE TABLE IF NOT EXISTS inventory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    producto VARCHAR(255) NOT NULL,
    stock_actual DECIMAL(10,2) NOT NULL,
    punto_reorden DECIMAL(10,2),
    cantidad_a_ordenar DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de configuración de análisis
CREATE TABLE IF NOT EXISTS analysis_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    lead_time INTEGER DEFAULT 7,
    stock_seguridad INTEGER DEFAULT 3,
    frecuencia INTEGER DEFAULT 7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de recetas (opcional)
CREATE TABLE IF NOT EXISTS recipes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    ingredientes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_sales_data_user_fecha ON sales_data(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_config_user ON analysis_config(user_id);
```

### 4️⃣ Configura el acceso público (RLS)

Desactiva temporalmente RLS o crea políticas públicas para testing:

```sql
-- Desactivar RLS para testing
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE sales_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE inventory DISABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_config DISABLE ROW LEVEL SECURITY;
ALTER TABLE recipes DISABLE ROW LEVEL SECURITY;
```

### 5️⃣ Deploy y Testing

1. **Guarda los cambios** en Netlify y haz **deploy**
2. Abre tu aplicación en el navegador
3. Abre la **consola del navegador** (F12 > Console)
4. Ejecuta: `window.diagnoseSupabase()`
5. Deberías ver: `✅ Using configuration from: VITE Environment Variables`

### 6️⃣ Verifica que todo funciona

**✅ Autenticación:**
- Intenta registrar un nuevo usuario
- Revisa en Supabase > Table Editor > `users` que aparezca el registro

**✅ Guardado de datos:**
- Sube un archivo CSV de ventas
- Revisa en Supabase > Table Editor > `sales_data` que aparezcan los datos

**✅ Dashboard:**
- Los KPIs deberían mostrar valores reales
- Los gráficos deberían funcionar con datos reales

## 🐛 Solución de Problemas

### ❌ "No database credentials found"
**Causa:** Las variables de entorno no están configuradas correctamente.
**Solución:** Verifica que en Netlify estén con el prefijo `VITE_` y redeploy.

### ❌ "Connected to Supabase" pero no guardan datos
**Causa:** Las tablas no existen o RLS está bloqueando el acceso.
**Solución:** Ejecuta el SQL del paso 3 y desactiva RLS para testing.

### ❌ Error 404/500 al conectar
**Causa:** URL o key incorrecta de Supabase.
**Solución:** Verifica que estés usando la URL correcta (https://tu-proyecto.supabase.co) y el anon key.

### ❌ Los datos no aparecen en el dashboard
**Causa:** El formato de datos no coincide con el esperado.
**Solución:** Verifica que los archivos CSV tengan el formato correcto.

## 📞 Soporte

Si tienes problemas:
1. Abre la consola del navegador y ejecuta `window.diagnoseSupabase()`
2. Toma una captura de pantalla del resultado
3. Verifica las variables de entorno en Netlify
4. Confirma que las tablas existen en Supabase

## 🎯 Checklist Final

- [ ] Variables VITE_SUPABASE_URL y VITE_SUPABASE_KEY configuradas en Netlify
- [ ] Deploy realizado después de configurar variables
- [ ] Tablas creadas en Supabase
- [ ] RLS desactivado o configurado correctamente
- [ ] `window.diagnoseSupabase()` muestra conexión exitosa
- [ ] Registro de usuarios funciona
- [ ] Guardado de datos funciona
- [ ] Dashboard muestra KPIs reales

¡Listo! Tu aplicación debería ahora estar completamente conectada a Supabase. 🚀
```