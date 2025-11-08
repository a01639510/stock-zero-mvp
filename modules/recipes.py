# modules/recipes.py

import streamlit as st
import pandas as pd

# ============================================
# RECETAS POR DEFECTO (EDITABLES)
# ============================================

RECETAS_DEFAULT = pd.DataFrame([
    {'platillo': 'Cappuccino', 'insumo': 'Café en Grano (Kg)', 'cantidad_por_unidad': 0.015, 'unidad': 'KG'},
    {'platillo': 'Cappuccino', 'insumo': 'Leche Entera (Litros)', 'cantidad_por_unidad': 0.2, 'unidad': 'L'},
    {'platillo': 'Latte', 'insumo': 'Café en Grano (Kg)', 'cantidad_por_unidad': 0.02, 'unidad': 'KG'},
    {'platillo': 'Latte', 'insumo': 'Leche Entera (Litros)', 'cantidad_por_unidad': 0.25, 'unidad': 'L'},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Carne Molida (Kg)', 'cantidad_por_unidad': 0.15, 'unidad': 'KG'},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Pan Hamburguesa (Uni)', 'cantidad_por_unidad': 1, 'unidad': 'UNI'},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Queso Cheddar (Uni)', 'cantidad_por_unidad': 1, 'unidad': 'UNI'},
    {'platillo': 'Pan de Muerto', 'insumo': 'Harina (Kg)', 'cantidad_por_unidad': 0.5, 'unidad': 'KG'},
    {'platillo': 'Pan de Muerto', 'insumo': 'Azúcar (Kg)', 'cantidad_por_unidad': 0.1, 'unidad': 'KG'},
])

# ============================================
# FUNCIÓN: CALCULAR INSUMOS GASTADOS
# ============================================

def calcular_insumos_gastados(df_ventas_platillos: pd.DataFrame, df_recetas: pd.DataFrame) -> pd.DataFrame:
    """Convierte ventas de platillos → insumos gastados por día."""
    if df_ventas_platillos.empty or df_recetas.empty:
        return pd.DataFrame(columns=['fecha', 'insumo', 'cantidad_gastada'])
    
    df_merge = df_ventas_platillos.merge(df_recetas, on='platillo', how='left')
    if df_merge.empty or 'cantidad_por_unidad' not in df_merge.columns:
        return pd.DataFrame(columns=['fecha', 'insumo', 'cantidad_gastada'])
    
    df_merge['cantidad_gastada'] = df_merge['cantidad_vendida'] * df_merge['cantidad_por_unidad']
    df_gastado = df_merge.groupby(['fecha', 'insumo'], as_index=False)['cantidad_gastada'].sum()
    df_gastado['fecha'] = pd.to_datetime(df_gastado['fecha']).dt.normalize()
    return df_gastado

# ============================================
# PÁGINA: GESTIÓN DE RECETAS
# ============================================

def recetas_app():
    st.header("Recetas y Productos")
    st.markdown("Administra las recetas para calcular insumos automáticamente.")

    # Cargar recetas actuales
    if 'df_recetas' not in st.session_state or st.session_state.df_recetas is None:
        st.session_state.df_recetas = RECETAS_DEFAULT.copy()

    df_recetas = st.session_state.df_recetas

    # Opciones
    tab1, tab2, tab3 = st.tabs(["Catálogo", "Subir CSV", "Exportar"])

    with tab1:
        st.subheader("Catálogo de Recetas")
        edited = st.data_editor(
            df_recetas, use_container_width=True, num_rows="dynamic", key="editor_recetas"
        )
        if st.button("Guardar Cambios", type="primary"):
            st.session_state.df_recetas = edited
            st.success("Recetas guardadas.")
            st.rerun()

    with tab2:
        st.subheader("Subir Recetas desde CSV")
        uploaded = st.file_uploader("CSV: platillo,insumo,cantidad_por_unidad,unidad", type="csv", key="upload_recetas")
        if uploaded:
            try:
                df_new = pd.read_csv(uploaded)
                required = ['platillo','insumo','cantidad_por_unidad','unidad']
                if all(col in df_new.columns for col in required):
                    st.session_state.df_recetas = df_new[required].copy()
                    st.success("Recetas cargadas desde CSV.")
                    st.rerun()
                else:
                    st.error(f"Faltan columnas: {required}")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab3:
        st.subheader("Exportar Recetas")
        csv = st.session_state.df_recetas.to_csv(index=False)
        st.download_button("Descargar CSV", csv, "recetas.csv", "text/csv")
