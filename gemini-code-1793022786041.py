import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador POA 2027 - Comfaboy", layout="wide")
st.title("🎯 Simulador Institucional de Tarifas y Subsidios (POA 2027)")
st.markdown("Basado en el formato oficial de *Información Tarifas (4-070)*. Selecciona un servicio para analizar su línea base y proyectar su comportamiento financiero.")

st.sidebar.header("📁 1. Carga de Base de Datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo '4-070. INFORMACIÓN TARIFAS.xlsx'", type=['xlsx', 'xls'])

if uploaded_file:
    try:
        df_catalogo = pd.read_excel(uploaded_file)
        
        # Validar que tenga las columnas esperadas
        columnas_req = ['Infraestructura', 'Concepto de la Tarifa', 'Servicio Social', 'Categoría', 'Costo Unitario Concepto', 'Valor Tarifa', 'Valor Tarifa Año Anterior']
        if not all(col in df_catalogo.columns for col in columnas_req):
            st.error(f"El archivo no tiene el formato correcto. Faltan algunas de estas columnas: {', '.join(columnas_req)}")
        else:
            st.sidebar.success(f"✅ Archivo cargado: {len(df_catalogo)} registros y {df_catalogo['Concepto de la Tarifa'].nunique()} conceptos.")
            
            # Selector de Concepto
            conceptos = sorted(df_catalogo['Concepto de la Tarifa'].dropna().astype(str).unique())
            concepto_seleccionado = st.sidebar.selectbox("🔍 Selecciona el Concepto a Tarifar:", conceptos)
            
            # Filtrar datos del concepto seleccionado
            df_filtro = df_catalogo[df_catalogo['Concepto de la Tarifa'] == concepto_seleccionado].copy()
            
            # Extraer meta-datos generales (asumiendo que son iguales para todas las categorías del mismo concepto)
            infraestructura = df_filtro['Infraestructura'].iloc[0] if not df_filtro.empty else "N/A"
            servicio_social = df_filtro['Servicio Social'].iloc[0] if not df_filtro.empty else "N/A"
            costo_unitario = float(df_filtro['Costo Unitario Concepto'].iloc[0]) if not df_filtro.empty else 0.0
            
            st.header(f"🛠️ {concepto_seleccionado}")
            st.markdown(f"**Infraestructura:** {infraestructura} | **Servicio Social:** {servicio_social}")
            
            st.markdown("---")
            st.header("2. Línea Base (Valores Actuales vs Año Anterior)")
            st.write(f"📌 **Costo Unitario del Concepto (Punto de Equilibrio):** ${costo_unitario:,.2f}")
            
            # Preparar tabla de línea base extraída del archivo
            categorias_ordenadas = ['A', 'B', 'C', 'D', 'EMPRESAS']
            df_filtro['Categoría'] = pd.Categorical(df_filtro['Categoría'], categories=categorias_ordenadas, ordered=True)
            df_filtro = df_filtro.sort_values('Categoría').dropna(subset=['Categoría'])
            
            # Diccionarios para guardar tarifas actuales
            tarifas_actuales = {}
            tarifas_anteriores = {}
            
            for _, row in df_filtro.iterrows():
                cat = row['Categoría']
                tarifas_actuales[cat] = float(row['Valor Tarifa'])
                tarifas_anteriores[cat] = float(row['Valor Tarifa Año Anterior'])
                
            df_linea_base = pd.DataFrame({
                "Categoría": df_filtro['Categoría'],
                "Tarifa Año Anterior": df_filtro['Valor Tarifa Año Anterior'],
                "Tarifa Actual (Archivo)": df_filtro['Valor Tarifa'],
                "Esfuerzo de Caja (Subsidio Actual)": costo_unitario - df_filtro['Valor Tarifa']
            }).set_index("Categoría")
            
            st.dataframe(df_linea_base.style.format("${:,.2f}").map(
                lambda x: 'color: green' if x < 0 else ('color: red' if x > 0 else ''),
                subset=["Esfuerzo de Caja (Subsidio Actual)"]
            ), use_container_width=True)
            st.caption("*(Valores en Rojo = Subsidio otorgado por la caja. Valores en Verde = Margen a favor)*")

            # --- PASO 3: SIMULACIÓN POA 2027 ---
            st.markdown("---")
            st.header("3. Simulación de Tarifas y Demanda (POA 2027)")
            st.write("Fija las nuevas tarifas propuestas para el próximo año y proyecta la demanda para obtener el P&G esperado.")
            
            col_t, col_d = st.columns(2)
            
            nuevas_tarifas = {}
            demanda_proyectada = {}
            
            with col_t:
                st.subheader("Nuevas Tarifas Propuestas [$]")
                for cat in categorias_ordenadas:
                    if cat in tarifas_actuales:
                        nuevas_tarifas[cat] = st.number_input(f"Tarifa Cat. {cat}", value=tarifas_actuales[cat], step=1000.0)
                        
            with col_d:
                st.subheader("Demanda Proyectada (Unidades)")
                # Valores por defecto de ejemplo
                default_demanda = {'A': 600, 'B': 200, 'C': 150, 'D': 30, 'EMPRESAS': 20}
                for cat in categorias_ordenadas:
                    if cat in tarifas_actuales:
                        demanda_proyectada[cat] = st.number_input(f"Usos/Ventas Cat. {cat}", min_value=0, value=default_demanda.get(cat, 0), step=10)

            # --- PASO 4: RESULTADOS FINANCIEROS (P&G) ---
            st.markdown("---")
            st.header("4. Estado de Resultados Proyectado (P&G)")
            
            total_unidades = sum(demanda_proyectada.values())
            costo_total_operacion = costo_unitario * total_unidades
            
            ingresos_totales = sum(demanda_proyectada[cat] * nuevas_tarifas[cat] for cat in nuevas_tarifas)
            
            # Subsidio otorgado (solo si el costo es mayor a la tarifa)
            subsidio_demanda = sum(
                demanda_proyectada[cat] * (costo_unitario - nuevas_tarifas[cat]) 
                for cat in nuevas_tarifas if nuevas_tarifas[cat] < costo_unitario
            )
            
            # Margen cruzado (cuando la tarifa D o Empresas es mayor al costo)
            margen_cruzado = sum(
                demanda_proyectada[cat] * (nuevas_tarifas[cat] - costo_unitario) 
                for cat in nuevas_tarifas if nuevas_tarifas[cat] > costo_unitario
            )
            
            resultado_operativo = ingresos_totales - costo_total_operacion
            
            df_pg = pd.DataFrame({
                "Indicador Financiero": [
                    "Total Unidades Proyectadas",
                    "Costos Totales de Operación (Proyectados)", 
                    "Ingresos Recaudados (Tarifas)", 
                    "Subsidio a la Demanda (Esfuerzo Caja)",
                    "Margen Cruzado a Favor (Excedentes)",
                    "RESULTADO NETO (Superávit / Déficit)"
                ],
                "Simulación POA 2027": [
                    total_unidades,
                    costo_total_operacion,
                    ingresos_totales,
                    subsidio_demanda,
                    margen_cruzado,
                    resultado_operativo
                ]
            }).set_index("Indicador Financiero")
            
            st.dataframe(df_pg.style.format({
                "Simulación POA 2027": lambda x: f"{x:,.0f}" if x == total_unidades else f"${x:,.2f}"
            }).map(
                lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else ('color: green' if isinstance(x, (int, float)) and x > 0 else ''),
                subset=["Simulación POA 2027"]
            ), use_container_width=True)
            
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
else:
    st.info("👈 Por favor, carga el archivo '4-070. INFORMACIÓN TARIFAS.xlsx' en el panel lateral.")