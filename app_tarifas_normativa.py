import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador POA 2027 - Comfaboy", layout="wide")
st.title("🎯 Simulador Institucional de Tarifas y Subsidios (POA 2027)")
st.markdown("Basado en el formato oficial de *Información Tarifas (4-070)*, la **Metodología de Tarifas 2026** y la **Circular 017 de 2014 de la Supersubsidio**.")

st.sidebar.header("📁 1. Carga de Base de Datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo '4-070. INFORMACIÓN TARIFAS.xlsx'", type=['xlsx', 'xls'])

if uploaded_file:
    try:
        df_catalogo = pd.read_excel(uploaded_file)
        
        columnas_req = ['Infraestructura', 'Concepto de la Tarifa', 'Servicio Social', 'Categoría', 'Costo Unitario Concepto', 'Valor Tarifa', 'Valor Tarifa Año Anterior']
        if not all(col in df_catalogo.columns for col in columnas_req):
            st.error(f"Faltan columnas en el archivo: {', '.join(columnas_req)}")
        else:
            st.sidebar.success(f"✅ Archivo cargado con éxito.")
            
            conceptos = sorted(df_catalogo['Concepto de la Tarifa'].dropna().astype(str).unique())
            concepto_seleccionado = st.sidebar.selectbox("🔍 Selecciona el Concepto a Tarifar:", conceptos)
            
            df_filtro = df_catalogo[df_catalogo['Concepto de la Tarifa'] == concepto_seleccionado].copy()
            
            infraestructura = df_filtro['Infraestructura'].iloc[0] if not df_filtro.empty else "N/A"
            servicio_social = df_filtro['Servicio Social'].iloc[0] if not df_filtro.empty else "N/A"
            costo_unitario_archivo = float(df_filtro['Costo Unitario Concepto'].iloc[0]) if not df_filtro.empty else 0.0
            
            st.header(f"🛠️ {concepto_seleccionado}")
            st.markdown(f"**Infraestructura:** {infraestructura} | **Servicio Social:** {servicio_social}")
            
            # --- NUEVO PASO: ESTUDIO TÉCNICO DE COSTOS ---
            st.markdown("---")
            st.header("2. Estudio Técnico de Costos (Modificador de Costo Unitario)")
            st.write("De acuerdo a la **Metodología 2026**, ajusta los insumos para calcular el nuevo Costo Unitario. Según la **Circular 017/2014**, las Depreciaciones/Amortizaciones no se incluyen como egresos efectivos para el cálculo del subsidio a la oferta.")
            
            usar_calculadora = st.radio("¿Cómo deseas establecer el Costo Unitario para 2027?", 
                                        ["Usar el costo actual del archivo", "Calcular nuevo costo por absorción (Insumos)"], horizontal=True)
            
            if usar_calculadora == "Calcular nuevo costo por absorción (Insumos)":
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    cf_efectivos = st.number_input("Costos Fijos (Nómina, Arriendos, etc.) [$]", min_value=0.0, value=5000000.0, step=500000.0)
                    depreciaciones = st.number_input("Depreciaciones, Amortizaciones y Provisiones (DAP) [$]", min_value=0.0, value=500000.0, step=100000.0)
                with col_c2:
                    cv_unitario = st.number_input("Costo Variable Unitario [$]", min_value=0.0, value=5000.0, step=500.0)
                with col_c3:
                    unidades_base_costeo = st.number_input("Unidades Base para Cálculo (Capacidad/Demanda)", min_value=1, value=1000, step=10)
                
                # Cálculo de costo unitario total (referente para tarifas)
                costo_fijo_unit = (cf_efectivos + depreciaciones) / unidades_base_costeo
                costo_unitario = costo_fijo_unit + cv_unitario
                
                # Costo unitario efectivo (sin depreciación - Para subsidio a la oferta)
                costo_unitario_efectivo = (cf_efectivos / unidades_base_costeo) + cv_unitario
                
                st.info(f"📌 **Nuevo Costo Unitario Referente:** ${costo_unitario:,.2f} | **Costo Unitario Efectivo (Sin DAP):** ${costo_unitario_efectivo:,.2f}")
            else:
                costo_unitario = costo_unitario_archivo
                costo_unitario_efectivo = costo_unitario_archivo
                cf_efectivos, cv_unitario, depreciaciones = 0, 0, 0
                st.info(f"📌 **Costo Unitario Base (Archivo):** ${costo_unitario:,.2f}")

            # --- PASO 3: LÍNEA BASE ACTUAL ---
            st.markdown("---")
            st.header("3. Línea Base (Valores Actuales)")
            categorias_ordenadas = ['A', 'B', 'C', 'D', 'EMPRESAS']
            df_filtro['Categoría'] = pd.Categorical(df_filtro['Categoría'], categories=categorias_ordenadas, ordered=True)
            df_filtro = df_filtro.sort_values('Categoría').dropna(subset=['Categoría'])
            
            tarifas_actuales = {}
            for _, row in df_filtro.iterrows():
                cat = row['Categoría']
                tarifas_actuales[cat] = float(row['Valor Tarifa'])
                
            df_linea_base = pd.DataFrame({
                "Categoría": df_filtro['Categoría'],
                "Tarifa Actual": df_filtro['Valor Tarifa'],
                "Esfuerzo de Caja (Costo - Tarifa)": costo_unitario_archivo - df_filtro['Valor Tarifa']
            }).set_index("Categoría")
            st.dataframe(df_linea_base.style.format("${:,.2f}").map(
                lambda x: 'color: green' if isinstance(x, float) and x < 0 else ('color: red' if isinstance(x, float) and x > 0 else ''),
                subset=["Esfuerzo de Caja (Costo - Tarifa)"]
            ), use_container_width=True)

            # --- PASO 4: SIMULACIÓN POA 2027 ---
            st.markdown("---")
            st.header("4. Simulación de Tarifas y Demanda (POA 2027)")
            
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
                default_demanda = {'A': 600, 'B': 200, 'C': 150, 'D': 30, 'EMPRESAS': 20}
                for cat in categorias_ordenadas:
                    if cat in tarifas_actuales:
                        demanda_proyectada[cat] = st.number_input(f"Usos/Ventas Cat. {cat}", min_value=0, value=default_demanda.get(cat, 0), step=10)

            # --- PASO 5: RESULTADOS FINANCIEROS Y SUBSIDIOS (CIRCULAR 017) ---
            st.markdown("---")
            st.header("5. Estado de Resultados y Aplicación de Subsidios (Circular 017/2014)")
            
            total_unidades = sum(demanda_proyectada.values())
            ingresos_totales = sum(demanda_proyectada[cat] * nuevas_tarifas[cat] for cat in nuevas_tarifas)
            
            # Cálculo de Egresos Efectivos (Sin DAP)
            if usar_calculadora == "Calcular nuevo costo por absorción (Insumos)":
                egresos_efectivos = cf_efectivos + (cv_unitario * total_unidades)
            else:
                egresos_efectivos = costo_unitario_efectivo * total_unidades
                
            # Subsidio a la Demanda (Cat A y B) - Diferencia entre el costo y la tarifa pagada
            sub_dem_A = demanda_proyectada.get('A', 0) * max(0, costo_unitario - nuevas_tarifas.get('A', 0))
            sub_dem_B = demanda_proyectada.get('B', 0) * max(0, costo_unitario - nuevas_tarifas.get('B', 0))
            subsidio_demanda_total = sub_dem_A + sub_dem_B
            
            # Resultado Operativo Inicial (Para verificar si hay déficit)
            resultado_operativo = ingresos_totales - egresos_efectivos
            
            # Cálculo Subsidio a la Oferta (Numeral 5.4.1 de la Circular 017)
            # Faltante = (Ingresos Totales + Subsidio a la Demanda) - Egresos (sin depreciaciones)
            cobertura = ingresos_totales + subsidio_demanda_total - egresos_efectivos
            subsidio_oferta = abs(cobertura) if cobertura < 0 else 0.0
            
            margen_cruzado = sum(
                demanda_proyectada[cat] * (nuevas_tarifas[cat] - costo_unitario) 
                for cat in nuevas_tarifas if nuevas_tarifas[cat] > costo_unitario
            )
            
            df_pg = pd.DataFrame({
                "Indicador Normativo": [
                    "Total Unidades Proyectadas",
                    "Ingresos Totales (Tarifas Recaudadas)", 
                    "Egresos Efectivos (Sin Depreciaciones/Amortizaciones)", 
                    "Subsidio a la Demanda (Cat A y B)",
                    "Resultado Operativo (Ingresos - Egresos Efectivos)",
                    "Subsidio a la Oferta (Déficit a cubrir)",
                    "Margen Cruzado a Favor (Categorías C, D y Empresas)"
                ],
                "Simulación (Pesos)": [
                    total_unidades,
                    ingresos_totales,
                    egresos_efectivos,
                    subsidio_demanda_total,
                    resultado_operativo,
                    subsidio_oferta,
                    margen_cruzado
                ]
            }).set_index("Indicador Normativo")
            
            st.dataframe(df_pg.style.format({
                "Simulación (Pesos)": lambda x: f"{x:,.0f}" if x == total_unidades else f"${x:,.2f}"
            }).map(
                lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else ('color: green' if isinstance(x, (int, float)) and x > 0 else ''),
                subset=["Simulación (Pesos)"]
            ), use_container_width=True)
            
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
else:
    st.info("👈 Por favor, carga el archivo '4-070. INFORMACIÓN TARIFAS.xlsx' en el panel lateral.")
