# modules/recipes.py

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List

# ============================================
# FUNCIONES AUXILIARES PARA RECETAS
# ============================================

def generar_recetas_base(df_inventario: pd.DataFrame = None, use_example_data: bool = False) -> pd.DataFrame:
    """Genera un DataFrame base para las recetas/productos."""
    
    if use_example_data:
        # Datos de ejemplo
        data = {
            'Producto Final': ['Hamburguesa Clásica', 'Café Americano', 'Café con Leche'],
            'Categoría': ['Comida', 'Bebida', 'Bebida'],
            'Precio Venta': [85.0, 35.0, 45.0],
            'Tiempo Prep (min)': [15, 3, 5],
            'Activo': [True, True, True]
        }
        return pd.DataFrame(data)
    
    # Si no hay datos de ejemplo, crear DataFrame vacío con estructura
    return pd.DataFrame(columns=['Producto Final', 'Categoría', 'Precio Venta', 'Tiempo Prep (min)', 'Activo'])


def generar_ingredientes_base(use_example_data: bool = False) -> pd.DataFrame:
    """Genera un DataFrame base para ingredientes de recetas."""
    
    if use_example_data:
        # Datos de ejemplo con ingredientes
        data = {
            'Producto Final': [
                'Hamburguesa Clásica', 'Hamburguesa Clásica', 'Hamburguesa Clásica',
                'Café Americano', 'Café con Leche', 'Café con Leche'
            ],
            'Ingrediente': [
                'Pan Hamburguesa (Uni)', 'Carne Molida (Kg)', 'Queso (Kg)',
                'Café en Grano (Kg)', 'Café en Grano (Kg)', 'Leche Entera (Litros)'
            ],
            'Cantidad Requerida': [1.0, 0.15, 0.05, 0.015, 0.015, 0.15],
            'Unidad': ['UNI', 'KG', 'KG', 'KG', 'KG', 'L']
        }
        return pd.DataFrame(data)
    
    return pd.DataFrame(columns=['Producto Final', 'Ingrediente', 'Cantidad Requerida', 'Unidad'])


def calcular_costo_receta(
    df_receta_ingredientes: pd.DataFrame,
    df_inventario: pd.DataFrame,
    producto_final: str
) -> Dict[str, float]:
    """Calcula el costo total de una receta basándose en el inventario."""
    
    ingredientes_receta = df_receta_ingredientes[
        df_receta_ingredientes['Producto Final'] == producto_final
    ]
    
    if ingredientes_receta.empty:
        return {'costo_total': 0.0, 'ingredientes_faltantes': 0}
    
    costo_total = 0.0
    ingredientes_faltantes = 0
    
    for _, row in ingredientes_receta.iterrows():
        ingrediente = row['Ingrediente']
        cantidad_req = row['Cantidad Requerida']
        
        # Buscar el ingrediente en el inventario
        inv_row = df_inventario[df_inventario['Producto'] == ingrediente]
        
        if not inv_row.empty:
            costo_unitario = inv_row['Costo Unitario'].iloc[0]
            costo_ingrediente = cantidad_req * costo_unitario
            costo_total += costo_ingrediente
        else:
            ingredientes_faltantes += 1
    
    return {
        'costo_total': round(costo_total, 2),
        'ingredientes_faltantes': ingredientes_faltantes
    }


def calcular_margen_utilidad(precio_venta: float, costo_total: float) -> Dict[str, float]:
    """Calcula el margen de utilidad de un producto."""
    
    if precio_venta <= 0 or costo_total <= 0:
        return {'utilidad': 0.0, 'margen_porcentaje': 0.0}
    
    utilidad = precio_venta - costo_total
    margen_porcentaje = (utilidad / precio_venta) * 100
    
    return {
        'utilidad': round(utilidad, 2),
        'margen_porcentaje': round(margen_porcentaje, 2)
    }


def verificar_disponibilidad_receta(
    df_receta_ingredientes: pd.DataFrame,
    df_inventario: pd.DataFrame,
    producto_final: str,
    cantidad_producir: int = 1
) -> Dict:
    """Verifica si hay suficiente stock para producir una receta."""
    
    ingredientes_receta = df_receta_ingredientes[
        df_receta_ingredientes['Producto Final'] == producto_final
    ]
    
    if ingredientes_receta.empty:
        return {
            'puede_producir': False,
            'cantidad_maxima': 0,
            'ingredientes_faltantes': []
        }
    
    cantidad_maxima = float('inf')
    ingredientes_faltantes = []
    
    for _, row in ingredientes_receta.iterrows():
        ingrediente = row['Ingrediente']
        cantidad_req = row['Cantidad Requerida'] * cantidad_producir
        
        inv_row = df_inventario[df_inventario['Producto'] == ingrediente]
        
        if not inv_row.empty:
            stock_disponible = inv_row['Stock Actual'].iloc[0]
            
            if stock_disponible < cantidad_req:
                ingredientes_faltantes.append({
                    'ingrediente': ingrediente,
                    'requerido': cantidad_req,
                    'disponible': stock_disponible,
                    'faltante': cantidad_req - stock_disponible
                })
            
            # Calcular cuántas unidades se pueden producir con este ingrediente
            cant_posible = int(stock_disponible / row['Cantidad Requerida'])
            cantidad_maxima = min(cantidad_maxima, cant_posible)
        else:
            ingredientes_faltantes.append({
                'ingrediente': ingrediente,
                'requerido': cantidad_req,
                'disponible': 0,
                'faltante': cantidad_req
            })
            cantidad_maxima = 0
    
    return {
        'puede_producir': len(ingredientes_faltantes) == 0,
        'cantidad_maxima': int(cantidad_maxima) if cantidad_maxima != float('inf') else 0,
        'ingredientes_faltantes': ingredientes_faltantes
    }


# ============================================
# INTERFAZ DE RECETAS
# ============================================

def recetas_app():
    """Componente completo para la gestión de recetas y productos."""
    
    st.header("👨‍🍳 Gestión de Recetas y Productos")
    
    # Inicializar session state
    if 'recetas_df' not in st.session_state:
        st.session_state['recetas_df'] = generar_recetas_base(use_example_data=True)
    
    if 'ingredientes_recetas_df' not in st.session_state:
        st.session_state['ingredientes_recetas_df'] = generar_ingredientes_base(use_example_data=True)
    
    df_recetas = st.session_state['recetas_df']
    df_ingredientes = st.session_state['ingredientes_recetas_df']
    df_inventario = st.session_state.get('inventario_df', pd.DataFrame())
    
    # Crear pestañas internas
    tab_listado, tab_detalles, tab_analisis = st.tabs([
        "📋 Listado de Recetas",
        "🔍 Detalles y Edición",
        "📊 Análisis de Rentabilidad"
    ])
    
    # ============================================
    # TAB 1: LISTADO DE RECETAS
    # ============================================
    with tab_listado:
        st.subheader("📋 Productos y Recetas Activos")
        
        if df_recetas.empty:
            st.info("No hay recetas registradas. Agrega tu primera receta abajo.")
        else:
            # Calcular costos para todas las recetas
            df_display = df_recetas.copy()
            
            if not df_inventario.empty and not df_ingredientes.empty:
                costos = []
                margenes = []
                
                for producto in df_display['Producto Final']:
                    costo_info = calcular_costo_receta(df_ingredientes, df_inventario, producto)
                    costos.append(costo_info['costo_total'])
                    
                    precio = df_display[df_display['Producto Final'] == producto]['Precio Venta'].iloc[0]
                    margen_info = calcular_margen_utilidad(precio, costo_info['costo_total'])
                    margenes.append(margen_info['margen_porcentaje'])
                
                df_display['Costo'] = costos
                df_display['Margen %'] = margenes
                df_display['Utilidad'] = df_display['Precio Venta'] - df_display['Costo']
            
            # Mostrar métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Recetas", len(df_display))
            with col2:
                activas = df_display['Activo'].sum() if 'Activo' in df_display.columns else 0
                st.metric("Recetas Activas", activas)
            with col3:
                if 'Precio Venta' in df_display.columns:
                    precio_promedio = df_display['Precio Venta'].mean()
                    st.metric("Precio Promedio", f"${precio_promedio:.2f}")
            with col4:
                if 'Margen %' in df_display.columns:
                    margen_promedio = df_display['Margen %'].mean()
                    st.metric("Margen Promedio", f"{margen_promedio:.1f}%")
            
            # Tabla editable
            st.markdown("### Editar Recetas")
            edited_recetas = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                key="editor_recetas",
                column_config={
                    "Activo": st.column_config.CheckboxColumn("Activo", default=True),
                    "Precio Venta": st.column_config.NumberColumn("Precio Venta", format="$%.2f"),
                    "Costo": st.column_config.NumberColumn("Costo", format="$%.2f", disabled=True),
                    "Utilidad": st.column_config.NumberColumn("Utilidad", format="$%.2f", disabled=True),
                    "Margen %": st.column_config.NumberColumn("Margen %", format="%.1f%%", disabled=True)
                }
            )
            
            if not edited_recetas.equals(df_recetas):
                # Eliminar columnas calculadas antes de guardar
                cols_to_keep = ['Producto Final', 'Categoría', 'Precio Venta', 'Tiempo Prep (min)', 'Activo']
                st.session_state['recetas_df'] = edited_recetas[[col for col in cols_to_keep if col in edited_recetas.columns]]
        
        st.markdown("---")
        st.subheader("➕ Agregar Nueva Receta")
        
        col1, col2 = st.columns(2)
        with col1:
            nuevo_nombre = st.text_input("Nombre del Producto", key="nuevo_producto")
            nueva_categoria = st.selectbox("Categoría", ["Comida", "Bebida", "Postre", "Otro"])
        with col2:
            nuevo_precio = st.number_input("Precio de Venta", min_value=0.0, value=50.0, step=5.0)
            nuevo_tiempo = st.number_input("Tiempo de Preparación (min)", min_value=1, value=10)
        
        if st.button("➕ Agregar Receta", type="primary"):
            if nuevo_nombre:
                nueva_receta = pd.DataFrame([{
                    'Producto Final': nuevo_nombre,
                    'Categoría': nueva_categoria,
                    'Precio Venta': nuevo_precio,
                    'Tiempo Prep (min)': nuevo_tiempo,
                    'Activo': True
                }])
                st.session_state['recetas_df'] = pd.concat([df_recetas, nueva_receta], ignore_index=True)
                st.success(f"✅ Receta '{nuevo_nombre}' agregada exitosamente!")
                st.rerun()
            else:
                st.error("Por favor ingresa un nombre para el producto.")
    
    # ============================================
    # TAB 2: DETALLES Y EDICIÓN DE INGREDIENTES
    # ============================================
    with tab_detalles:
        st.subheader("🔍 Ingredientes por Receta")
        
        if df_recetas.empty:
            st.warning("Primero debes agregar recetas en la pestaña de Listado.")
        else:
            producto_seleccionado = st.selectbox(
                "Selecciona una receta para ver/editar ingredientes:",
                options=df_recetas['Producto Final'].tolist(),
                key="selector_receta_detalle"
            )
            
            if producto_seleccionado:
                st.markdown(f"### Ingredientes de: **{producto_seleccionado}**")
                
                # Mostrar ingredientes actuales
                ingredientes_producto = df_ingredientes[
                    df_ingredientes['Producto Final'] == producto_seleccionado
                ]
                
                if ingredientes_producto.empty:
                    st.info("Esta receta no tiene ingredientes asignados todavía.")
                else:
                    edited_ingredientes = st.data_editor(
                        ingredientes_producto,
                        use_container_width=True,
                        hide_index=True,
                        key=f"editor_ingredientes_{producto_seleccionado}",
                        num_rows="dynamic"
                    )
                    
                    # Actualizar en session state
                    otros_ingredientes = df_ingredientes[
                        df_ingredientes['Producto Final'] != producto_seleccionado
                    ]
                    st.session_state['ingredientes_recetas_df'] = pd.concat(
                        [otros_ingredientes, edited_ingredientes], 
                        ignore_index=True
                    )
                
                st.markdown("---")
                st.markdown("### ➕ Agregar Ingrediente a esta Receta")
                
                if df_inventario.empty:
                    st.warning("No hay productos en el inventario. Primero carga datos en la pestaña de Control de Inventario.")
                else:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        ingredientes_disponibles = df_inventario['Producto'].tolist()
                        nuevo_ingrediente = st.selectbox(
                            "Ingrediente",
                            options=ingredientes_disponibles,
                            key="nuevo_ingrediente"
                        )
                    
                    with col2:
                        nueva_cantidad = st.number_input(
                            "Cantidad",
                            min_value=0.0,
                            value=1.0,
                            step=0.1,
                            format="%.3f"
                        )
                    
                    with col3:
                        # Detectar unidad del ingrediente seleccionado
                        unidad_detectada = "UNI"
                        if not df_inventario.empty:
                            row_ing = df_inventario[df_inventario['Producto'] == nuevo_ingrediente]
                            if not row_ing.empty and 'Unidad' in row_ing.columns:
                                unidad_detectada = row_ing['Unidad'].iloc[0]
                        
                        nueva_unidad = st.text_input("Unidad", value=unidad_detectada, disabled=True)
                    
                    if st.button("➕ Agregar Ingrediente"):
                        nuevo_ing_df = pd.DataFrame([{
                            'Producto Final': producto_seleccionado,
                            'Ingrediente': nuevo_ingrediente,
                            'Cantidad Requerida': nueva_cantidad,
                            'Unidad': nueva_unidad
                        }])
                        st.session_state['ingredientes_recetas_df'] = pd.concat(
                            [df_ingredientes, nuevo_ing_df], 
                            ignore_index=True
                        )
                        st.success(f"✅ Ingrediente agregado a {producto_seleccionado}")
                        st.rerun()
    
    # ============================================
    # TAB 3: ANÁLISIS DE RENTABILIDAD
    # ============================================
    with tab_analisis:
        st.subheader("📊 Análisis de Rentabilidad y Disponibilidad")
        
        if df_recetas.empty or df_inventario.empty:
            st.warning("Necesitas tener recetas e inventario cargado para ver el análisis.")
        else:
            # Crear tabla de análisis
            analisis_data = []
            
            for _, receta in df_recetas.iterrows():
                producto = receta['Producto Final']
                precio_venta = receta['Precio Venta']
                
                # Calcular costo
                costo_info = calcular_costo_receta(df_ingredientes, df_inventario, producto)
                costo_total = costo_info['costo_total']
                
                # Calcular margen
                margen_info = calcular_margen_utilidad(precio_venta, costo_total)
                
                # Verificar disponibilidad
                disponibilidad = verificar_disponibilidad_receta(
                    df_ingredientes, df_inventario, producto
                )
                
                analisis_data.append({
                    'Producto': producto,
                    'Precio Venta': precio_venta,
                    'Costo': costo_total,
                    'Utilidad': margen_info['utilidad'],
                    'Margen %': margen_info['margen_porcentaje'],
                    'Puede Producir': disponibilidad['cantidad_maxima'],
                    'Ingredientes OK': '✅' if disponibilidad['puede_producir'] else '⚠️'
                })
            
            df_analisis = pd.DataFrame(analisis_data)
            
            # Métricas generales
            col1, col2, col3 = st.columns(3)
            with col1:
                margen_promedio = df_analisis['Margen %'].mean()
                st.metric("Margen Promedio", f"{margen_promedio:.1f}%")
            with col2:
                producto_mas_rentable = df_analisis.loc[df_analisis['Margen %'].idxmax(), 'Producto']
                st.metric("Más Rentable", producto_mas_rentable)
            with col3:
                productos_disponibles = (df_analisis['Puede Producir'] > 0).sum()
                st.metric("Productos Disponibles", f"{productos_disponibles}/{len(df_analisis)}")
            
            # Tabla de análisis
            st.dataframe(
                df_analisis,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Precio Venta": st.column_config.NumberColumn("Precio Venta", format="$%.2f"),
                    "Costo": st.column_config.NumberColumn("Costo", format="$%.2f"),
                    "Utilidad": st.column_config.NumberColumn("Utilidad", format="$%.2f"),
                    "Margen %": st.column_config.NumberColumn("Margen %", format="%.1f%%"),
                    "Puede Producir": st.column_config.NumberColumn("Unidades Disponibles", format="%d")
                }
            )
            
            # Simulador de producción
            st.markdown("---")
            st.markdown("### 🧮 Simulador de Producción")
            
            col1, col2 = st.columns(2)
            with col1:
                producto_simular = st.selectbox(
                    "Producto a producir:",
                    options=df_recetas['Producto Final'].tolist(),
                    key="producto_simular"
                )
            with col2:
                cantidad_simular = st.number_input(
                    "Cantidad a producir:",
                    min_value=1,
                    value=1,
                    step=1
                )
            
            if st.button("🔍 Verificar Disponibilidad"):
                resultado = verificar_disponibilidad_receta(
                    df_ingredientes, df_inventario, producto_simular, cantidad_simular
                )
                
                if resultado['puede_producir']:
                    st.success(f"✅ Puedes producir {cantidad_simular} unidades de {producto_simular}")
                    st.info(f"💡 Máximo producible con inventario actual: {resultado['cantidad_maxima']} unidades")
                else:
                    st.error(f"❌ No hay suficiente inventario para producir {cantidad_simular} unidades")
                    
                    if resultado['ingredientes_faltantes']:
                        st.markdown("**Ingredientes faltantes:**")
                        df_faltantes = pd.DataFrame(resultado['ingredientes_faltantes'])
                        st.dataframe(df_faltantes, use_container_width=True, hide_index=True)
