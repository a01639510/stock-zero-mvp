# modules/recipes.py

import streamlit as st
import pandas as pd
import numpy as np

# ============================================
# DATOS DE EJEMPLO (RECETAS)
# ============================================

RECETAS_EJEMPLO = pd.DataFrame([
    # Cappuccino
    {'platillo': 'Cappuccino', 'insumo': 'Café en Grano (Kg)', 'cantidad': 0.015, 'unidad': 'KG', 'costo_unitario': 25.0},
    {'platillo': 'Cappuccino', 'insumo': 'Leche Entera (Litros)', 'cantidad': 0.2, 'unidad': 'L', 'costo_unitario': 1.5},
    
    # Hamburguesa Clásica
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Carne Molida (Kg)', 'cantidad': 0.15, 'unidad': 'KG', 'costo_unitario': 18.0},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Pan Hamburguesa (Uni)', 'cantidad': 1, 'unidad': 'UNI', 'costo_unitario': 0.8},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Queso Cheddar (Uni)', 'cantidad': 1, 'unidad': 'UNI', 'costo_unitario': 1.2},
    
    # Pan de Muerto
    {'platillo': 'Pan de Muerto', 'insumo': 'Harina (Kg)', 'cantidad': 0.5, 'unidad': 'KG', 'costo_unitario': 12.0},
    {'platillo': 'Pan de Muerto', 'insumo': 'Azúcar (Kg)', 'cantidad': 0.1, 'unidad': 'KG', 'costo_unitario': 8.0},
    {'platillo': 'Pan de Muerto', 'insumo': 'Mantequilla (Kg)', 'cantidad': 0.1, 'unidad': 'KG', 'costo_unitario': 22.0},
])

# ============================================
# FUNCIÓN: CALCULAR INSUMOS GASTADOS
# ============================================

def calcular_insumos_gastados(df_ventas_platillos: pd.DataFrame, df_recetas: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte ventas de platillos en insumos gastados por día.
    """
    if df_ventas_platillos.empty or df_recetas.empty:
        return pd.DataFrame(columns=['fecha', 'insumo', 'cantidad_gastada', 'costo_total'])
    
    # Unir ventas con recetas
    df_merge = df_ventas_platillos.merge(df_recetas, on='platillo', how='left')
    
    if df_merge.empty:
        return pd.DataFrame(columns=['fecha', 'insumo', 'cantidad_gastada', 'costo_total'])
    
    # Calcular gasto
    df_merge['cantidad_gastada'] = df_merge['cantidad_vendida'] * df_merge['cantidad']
    df_merge['costo_total'] = df_merge['cantidad_gastada'] * df_merge['costo_unitario']
    
    # Agrupar por fecha e insumo
    df_resultado = df_merge.groupby(['fecha', 'insumo'], as_index=False).agg({
        'cantidad_gastada': 'sum',
        'costo_total': 'sum'
    })
    
    df_resultado['fecha'] = pd.to_datetime(df_resultado['fecha']).dt.normalize()
    
    return df_resultado

# ============================================
# FUNCIÓN: CALCULAR COSTOS Y MÁRGENES
# ============================================

def calcular_costos_margenes(df_recetas: pd.DataFrame, precio_venta: float, platillo: str) -> dict:
    """Calcula costo total, margen y precio sugerido."""
    df_platillo = df_recetas[df_recetas['platillo'] == platillo]
    if df_platillo.empty:
        return {}
    
    costo_total = (df_platillo['cantidad'] * df_platillo['costo_unitario']).sum()
    margen = ((precio_venta - costo_total) / precio_venta * 100) if precio_venta > 0 else 0
    precio_sugerido = costo_total * 3  # 200% margen sugerido
    
    return {
        'costo_total': round(costo_total, 2),
        'margen': round(margen, 1),
        'precio_sugerido': round(precio_sugerido, 2)
    }

# ============================================
# PÁGINA: RECETAS Y PRODUCTOS
# ============================================

def recetas_app():
    st.header("👨‍🍳 Recetas y Productos")
    st.markdown("Gestiona recetas, costos y disponibilidad de platillos.")

    # Inicializar recetas en session_state
    if 'df_recetas' not in st.session_state:
        st.session_state.df_recetas = RECETAS_EJEMPLO.copy()

    df_recetas = st.session_state.df_recetas

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Catálogo de Recetas", "💰 Costos y Márgenes", "📊 Disponibilidad", "⬇️ Exportar / Subir"])

    # ========================================
    # TAB 1: CATÁLOGO DE RECETAS
    # ========================================
    with tab1:
        st.subheader("Catálogo de Recetas")
        st.markdown("Edita, agrega o elimina insumos por platillo.")

        # Editor en vivo
        edited_df = st.data_editor(
            df_recetas,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "platillo": st.column_config.TextColumn("Platillo", required=True),
                "insumo": st.column_config.TextColumn("Insumo", required=True),
                "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.001, format="%.3f"),
                "unidad": st.column_config.SelectboxColumn("Unidad", options=["KG", "L", "UNI"]),
                "costo_unitario": st.column_config.NumberColumn("Costo Unitario ($)", min_value=0.0, format="$%.2f")
            },
            key="editor_recetas"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                st.session_state.df_recetas = edited_df.copy()
                st.success("Recetas guardadas correctamente.")
                st.rerun()
        with col2:
            if st.button("🔄 Restaurar Ejemplo", type="secondary", use_container_width=True):
                st.session_state.df_recetas = RECETAS_EJEMPLO.copy()
                st.success("Recetas restauradas al ejemplo.")
                st.rerun()

    # ========================================
    # TAB 2: COSTOS Y MÁRGENES
    # ========================================
    with tab2:
        st.subheader("Análisis de Costos y Márgenes")
        
        platillos = sorted(df_recetas['platillo'].unique())
        platillo_seleccionado = st.selectbox("Selecciona un platillo", platillos)
        
        precio_venta = st.number_input("Precio de Venta ($)", min_value=0.0, value=5.0, step=0.5)
        
        if platillo_seleccionado:
            info = calcular_costos_margenes(df_recetas, precio_venta, platillo_seleccionado)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💸 Costo Total", f"${info.get('costo_total', 0):.2f}")
            with col2:
                st.metric("📈 Margen Actual", f"{info.get('margen', 0):.1f}%")
            with col3:
                st.metric("🎯 Precio Sugerido", f"${info.get('precio_sugerido', 0):.2f}")
            
            if info.get('margen', 0) < 60:
                st.warning("⚠️ Margen bajo. Considera ajustar precio o costos.")
            else:
                st.success("✅ Margen saludable.")

    # ========================================
    # TAB 3: DISPONIBILIDAD (SIMULADA)
    # ========================================
    with tab3:
        st.subheader("Disponibilidad de Platillos")
        st.markdown("Simula cuántos platillos puedes preparar con el stock actual.")

        if 'inventario_df' in st.session_state and not st.session_state.inventario_df.empty:
            df_stock = st.session_state.inventario_df.set_index('Producto')['Stock Actual'].to_dict()
        else:
            df_stock = {}

        platillo_disp = st.selectbox("Platillo para simular", platillos, key="disp_platillo")
        
        df_insumos = df_recetas[df_recetas['platillo'] == platillo_disp]
        disponibilidad = []
        
        for _, row in df_insumos.iterrows():
            insumo = row['insumo']
            requerido = row['cantidad']
            stock_actual = df_stock.get(insumo, 0)
            max_posible = int(stock_actual // requerido) if requerido > 0 else 0
            disponibilidad.append({
                'insumo': insumo,
                'requerido': requerido,
                'stock_actual': stock_actual,
                'max_posible': max_posible
            })
        
        df_disp = pd.DataFrame(disponibilidad)
        if not df_disp.empty:
            max_platillos = df_disp['max_posible'].min()
            st.metric(f"🍽️ Máximo de **{platillo_disp}** posible", max_platillos)
            
            st.dataframe(
                df_disp[['insumo', 'requerido', 'stock_actual', 'max_posible']],
                column_config={
                    "insumo": "Insumo",
                    "requerido": "Req.",
                    "stock_actual": "Stock",
                    "max_posible": "Máx"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay insumos para este platillo.")

    # ========================================
    # TAB 4: EXPORTAR / SUBIR
    # ========================================
    with tab4:
        st.subheader("Exportar e Importar Recetas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**⬇️ Exportar Recetas**")
            csv_data = st.session_state.df_recetas.to_csv(index=False).encode()
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name="recetas_completas.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("**⬆️ Importar Recetas**")
            uploaded_file = st.file_uploader("Subir CSV", type=['csv'], key="upload_recetas_csv")
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_csv(uploaded_file)
                    required_cols = ['platillo', 'insumo', 'cantidad', 'unidad', 'costo_unitario']
                    if all(col in df_upload.columns for col in required_cols):
                        st.session_state.df_recetas = df_upload[required_cols].copy()
                        st.success("Recetas importadas correctamente.")
                        st.rerun()
                    else:
                        st.error(f"Faltan columnas: {required_cols}")
                except Exception as e:
                    st.error(f"Error al leer archivo: {e}")

    st.markdown("---")
    st.caption("💡 Usa el editor para personalizar recetas. Los cambios se guardan automáticamente.")
