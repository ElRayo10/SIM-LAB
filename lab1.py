import simpy
import random
import matplotlib.pyplot as plt

random.seed(42)

# ==========================================
# CONFIGURACIÓN DE LA LÍNEA Y PARADAS
# ==========================================
config_paradas = [
    {'nombre': 'Francesc Macià',    't_viaje': 3, 'tasa_base': 1.5},
    {'nombre': 'Reina M. Cristina', 't_viaje': 2, 'tasa_base': 2.0},
    {'nombre': 'Zona Universitària','t_viaje': 3, 'tasa_base': 2.5},
    {'nombre': 'Hospital-TV3',      't_viaje': 5, 'tasa_base': 3.0},
    {'nombre': 'Sant Feliu',        't_viaje': 5, 'tasa_base': 4.0},
    {'nombre': 'Molins de Rei',     't_viaje': 3, 'tasa_base': 4.5},
    {'nombre': 'Sant Vicenç H.',    't_viaje': 2, 'tasa_base': 6.0},
    {'nombre': 'Cervelló',          't_viaje': 3, 'tasa_base': 8.0},
    {'nombre': 'Vallirana',         't_viaje': 0, 'tasa_base': 10.0}
]

def simular_linea_completa(tiempo_fin=720): # Simulamos 12 horas (720 min)
    env = simpy.Environment()
    
    paradas = []
    for conf in config_paradas:
        paradas.append({
            'nombre': conf['nombre'],
            'recurso': simpy.Resource(env, capacity=1),
            't_viaje': conf['t_viaje'],
            'tasa_base': conf['tasa_base'],
            'cola': 0,
            'lst_bus': 0,
            'total_pasajeros_subidos': 0  # NUEVO: Estadística de volumen
        })
        
    datos_intervalos = []
    
    # NUEVO: Diccionarios para registrar las colas minuto a minuto
    datos_colas = {'Francesc Macià': [], 'Hospital-TV3': [], 'Tiempos': []}

    # --- Proceso Espía (Monitor de colas) ---
    def monitor_colas():
        while True:
            datos_colas['Tiempos'].append(env.now)
            # Guardamos la cola de la parada 0 (F. Macià) y 3 (Hosp-TV3)
            datos_colas['Francesc Macià'].append(paradas[0]['cola'])
            datos_colas['Hospital-TV3'].append(paradas[3]['cola'])
            yield env.timeout(1) # Toma una muestra cada minuto

    # --- Generador de Pasajeros (Demanda Variable) ---
    def gen_pasajeros(parada):
        while True:
            es_hora_punta = (0 <= env.now <= 120) or (360 <= env.now <= 480)
            multiplicador = 0.5 if es_hora_punta else 1.5
            tasa_actual = parada['tasa_base'] * multiplicador
            
            yield env.timeout(random.expovariate(1.0 / tasa_actual))
            parada['cola'] += 1

    # --- Ruta de los Autobuses ---
    def autobus(id_bus):
        while True:
            for i, parada in enumerate(paradas):
                with parada['recurso'].request() as req:
                    yield req
                    
                    if parada['nombre'] == 'Francesc Macià':
                        hueco = env.now - parada['lst_bus']
                        if env.now > 20: 
                            datos_intervalos.append((env.now, hueco))
                        parada['lst_bus'] = env.now

                    # NUEVO: Contabilizar pasajeros que suben
                    pasajeros_en_parada = parada['cola']
                    parada['total_pasajeros_subidos'] += pasajeros_en_parada
                    
                    # Embarque: 0.2 minutos (12 seg) por persona
                    tiempo_embarque = pasajeros_en_parada * 0.2
                    parada['cola'] = 0
                    yield env.timeout(tiempo_embarque)
                
                if parada['t_viaje'] > 0:
                    yield env.timeout(max(0, random.normalvariate(parada['t_viaje'], 0.5)))
            
            # Retorno en vacío a Barcelona
            yield env.timeout(30)

    # --- Inicialización ---
    for p in paradas:
        env.process(gen_pasajeros(p))

    def despachar_flota():
        for i in range(5):
            env.process(autobus(i+1))
            yield env.timeout(15) # Intervalo inicial ideal de 15 min
            
    env.process(despachar_flota())
    env.process(monitor_colas()) # Iniciamos el monitor de colas

    print("Simulando línea completa (5 buses, 9 paradas, demanda variable)...")
    env.run(until=tiempo_fin)
    
    return datos_intervalos, datos_colas, paradas

# ==========================================
# EJECUCIÓN 
# ==========================================
datos_intervalos, datos_colas, stats_paradas = simular_linea_completa(720)

# ==========================================
# IMPRESIÓN DE ESTADÍSTICAS POR CONSOLA
# ==========================================
print("\n" + "="*50)
print("📊 ESTADÍSTIQUES FINALS DE LA LÍNIA (720 minuts)")
print("="*50)
total_red = 0
for p in stats_paradas:
    print(f"Parada: {p['nombre']:<20} | Passatgers atesos: {p['total_pasajeros_subidos']}")
    total_red += p['total_pasajeros_subidos']
print("-" * 50)
print(f"🚌 TOTAL PASSATGERS TRANSPORTATS: {total_red}")
print("="*50)

# ==========================================
# GENERACIÓN DE GRÁFICOS (DOBLE PANEL)
# ==========================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# --- Gráfico 1: Bus Bunching (Intervalos) ---
tiempos_int = [p[0] for p in datos_intervalos]
huecos = [p[1] for p in datos_intervalos]

ax1.plot(tiempos_int, huecos, linestyle='-', marker='o', color='blue', markersize=3, alpha=0.7)
ax1.axvspan(0, 120, color='red', alpha=0.1, label='Hora Punta (Matí)')
ax1.axvspan(360, 480, color='red', alpha=0.1, label='Hora Punta (Migdia)')
ax1.axhline(y=15, color='green', linestyle='--', label='Interval Ideal (15 min)')

ax1.set_title("Efecte Acordió: Interval entre Autobusos a F. Macià", fontsize=14, fontweight='bold')
ax1.set_ylabel("Interval (minuts)", fontsize=12)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.set_ylim(bottom=0)

# --- Gráfico 2: Evolución de las Colas ---
t_colas = datos_colas['Tiempos']
c_fm = datos_colas['Francesc Macià']
c_htv = datos_colas['Hospital-TV3']

ax2.plot(t_colas, c_fm, color='darkorange', linewidth=1.5, label='Cua a Francesc Macià')
ax2.plot(t_colas, c_htv, color='purple', linewidth=1.5, alpha=0.7, label='Cua a Hospital-TV3')

# Ajustamos los márgenes para que no se corte nada
plt.tight_layout()

# 1. GUARDAMOS LA IMAGEN EN TU CARPETA (Alta calidad para el PDF)
plt.savefig('grafics_laboratori_SIM.png', dpi=300, bbox_inches='tight')
print("✅ Gràfics guardats correctament com a 'grafics_laboratori_SIM.png'")

# 2. Intentamos mostrarla (por si acaso el backend responde)
try:
    plt.show()
except:
    pass