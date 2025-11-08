# modules/recipes.py

import streamlit as st
import pandas as pd
import numpy as np

# ============================================
# DATOS DE EJEMPLO (RECETAS)
# ============================================

RECETAS_EJEMPLO = pd.DataFrame([
    # Cappuccino
    {'platillo': 'Cappuccino', 'insumo': 'Café en Grano (Kg)', 'cantidad_por_unidad': 0.015, 'unidad': 'KG', 'costo_unitario': 25.0},
    {'platillo': 'Cappuccino', 'insumo': 'Leche Entera (Litros)', 'cantidad_por_unidad': 0.2, 'unidad': 'L', 'costo_unitario': 1.5},
    
    # Hamburguesa Clásica
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Carne Molida (Kg)', 'cantidad_por_unidad': 0.15, 'unidad': 'KG', 'costo_unitario': 18.0},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Pan Hamburguesa (Uni)', 'cantidad_por_unidad': 1, 'unidad': 'UNI', 'costo_unitario': 0.8},
    {'platillo': 'Hamburguesa Clásica', 'insumo': 'Queso Cheddar (Uni)', 'cantidad_por_unidad': 1, 'unidad': 'UNI', 'costo_unitario': 1.2},
    
    # Pan de Muerto
    {'platillo': 'Pan de Muerto', 'insumo': 'Harina (Kg)', 'cantidad_por_unidad': 0.5, 'unidad': 'KG', 'costo_unitario': 12.0},
    {'platillo': 'Pan de Muerto', 'insumo': 'Azúcar (Kg)', 'cantidad_por_unidad': 0.1, 'unidad': 'KG', 'costo_unitario': 8.0},
    {'platillo': 'Pan de Muerto', 'insumo': 'Mantequilla (Kg)', 'cantidad_por_unidad': 0.1, 'unidad': 'KG', 'costo_unitario': 22.0},
])

# ============================================
# FUNCIÓN: CALCULAR INSUMOS GASTADOS
# ============================================

def calcular_insumos_gastados(df_ventas_platillos: pd.DataFrame, df_recetas: pd.DataFrame) -> pd.DataFrame:
    if df_ventas_platillos.empty or df_recetas.empty:
        return pd.DataFrame(columns=['fecha', 'insumo', 'cantidad_gastada', 'costo_total'])
    
    df_merge = df_ventas_platillos.merge(df_recetas, on='platillo', how='left')
    
    if df_merge.empty:
        return pd.DataFrame(columns=['fecha', 'insumo', 'cantidad_gastada', 'costo_total'])
    
    df_merge['cantidad_gastada'] = df_merge['cantidad_vendida'] * df_merge['cantidad_por_unidad']
    df_merge['costo_total'] = df_merge['cantidad_gastada'] * df_merge['costo_unitario']
    
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
    df_platillo = df_recetas[df_recetas['platillo'] == platillo]
    if df_platillo.empty:
        return {}
    
    costo_total = (df_platillo['cantidad_por_unidad'] * df_platillo['costo_unitario']).sum()
    margen = ((precio_venta - costo_total) / precio_venta * 100) if precio_venta > 0 else 0
    precio_sugerido = costo_total * 3
    
    return {
        'costo_total': round(costo_total, 2),
        'margen': round(margen, 1),
        'precio_sugerido': round(precio_sugerido, 2)
    }

# ============================================
# PÁGINA: RECETAS Y PRODUCTOS
# ============================================

def recetas_app():
    st.header("Recetas y Productos")
    st.markdown("Gestiona recetas, costos y disponibilidad de platillos.")

    if 'df_recetas' not in st.session_state:
        st.session_state.df_recetas = RECETAS_EJEMPLO.copy()

    df_recetas = st.session_state.df_recetas

    tab1, tab2, tab3, tab4 = st.tabs(["Catálogo", "Costos", "Disponibilidad", "Exportar"])

    with tab1:
        st.subheader("Catálogo de Recetas")
        edited_df = st.data_editor(
            df_recetas,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "platillo": st.column_config.TextColumn("Platillo", required=True),
                "insumo": st.column_config.TextColumn("Insumo", required=True),
                "cantidad_por_unidad": st.column_config.NumberColumn("Cant. por Unidad", min_value=0.001, format="%.3f"),
                "unidad": st.column_config.SelectboxColumn("Unidad", options=["KG", "L", "UNI"]),
                "costo_unitario": st.column_config.NumberColumn("Costo Unitario ($)", min_value=0.0, format="$%.2f")
            },
            key="editor_recetas"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Guardar Cambios", type="primary"):
                st.session_state.df_recetas = edited_df.copy()
                st.success("Guardado.")
                st.rerun()
        with col2:
            if st.button("Restaurar Ejemplo"):
                st.session_state.df_recetas = RECETAS_EJEMPLO.copy()
                st.success("Restaurado.")
                st.rerun()

    with tab2:
        st.subheader("Costos y Márgenes")
        platillos = sorted(df_recetas['platillo'].unique())
        platillo = st.selectbox("Platillo", platillos)
        precio_venta = st.number_input("Precio de Venta ($)", min_value=0.0, value=5.0, step=0.5)
        
        if platillo:
            info = calcular_costos_margenes(df_recetas, precio_venta, platillo)
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Costo Total", f"${info.get('costo_total', 0):.2f}")
            with c2: st.metric("Margen", f"{info.get('margen', 0):.1f}%")
            with c3: st.metric("Precio Sugerido", f"${info.get('precio_sugerido', 0):.2f}")

    with tab3:
        st.subheader("Disponibilidad")
        if 'inventario_df' in st.session_state and not st.session_state.inventario_df.empty:
            stock_dict = st.session_state.inventario_df.set_index('Producto')['Stock Actual'].to_dict()
        else:
            stock_dict = {}

        platillo_disp = st.selectbox("Platillo", platillos, key="disp")
        df_ins = df_recetas[df_recetas['platillo'] == platillo_disp]
        disp = []
        for _, r in df_ins.iterrows():
            ins = r['insumo']
            req = r['cantidad_por_unidad']
            stock = stock_dict.get(ins, 0)
            max_p = int(stock // req) if req > 0 else 0
            disp.append({'insumo': ins, 'requerido': req, 'stock': stock, 'max': max_p})
        
        df_disp = pd.DataFrame(disp)
        if not df_disp.empty:
            st.metric(f"Máximo de **{platillo_disp}**", df_disp['max'].min())
            st.dataframe(df_disp[['insumo', 'requerido', 'stock', 'max']], use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Exportar / Importar")
        col1, col2 = st.columns(2)
        with col1:
            csv = st.session_state.df_recetas.to_csv(index=False).encode()
            st.download_button("Descargar CSV", csv, "recetas.csv", "text/csv")
        with col2:
            up = st.file_uploader("Subir CSV", type="csv")
            if up:
                df_up = pd.read_csv(up)
                req = ['platillo','insumo','cantidad_por_unidad','unidad','costo_unitario']
                if all(c in df_up.columns for c in req):
                    st.session_state.df_recetas = df_up[req].copy()
                    st.success("Importado.")
                    st.rerun()
                else:
                    st.error(f"Faltan: {req}")
