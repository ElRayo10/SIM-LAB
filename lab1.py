import simpy
import random
import matplotlib.pyplot as plt

random.seed(42)

# ==========================================
# CONFIGURACIÓN (Opciones A, B y C)
# ==========================================
CAPACITAT_MAXIMA = 50  # Opción B
INTERVAL_IDEAL = 15    # Opción C (Minutos de Holding)

config_paradas = [
    {'nombre': 'Francesc Macià',    't_viaje': 3, 'tasa_base': 1.5, 'ratio_bajada': 0.0},
    {'nombre': 'Reina M. Cristina', 't_viaje': 2, 'tasa_base': 2.0, 'ratio_bajada': 0.1},
    {'nombre': 'Zona Universitària','t_viaje': 3, 'tasa_base': 2.5, 'ratio_bajada': 0.2},
    {'nombre': 'Hospital-TV3',      't_viaje': 5, 'tasa_base': 3.0, 'ratio_bajada': 0.3},
    {'nombre': 'Sant Feliu',        't_viaje': 5, 'tasa_base': 4.0, 'ratio_bajada': 0.2},
    {'nombre': 'Molins de Rei',     't_viaje': 3, 'tasa_base': 4.5, 'ratio_bajada': 0.2},
    {'nombre': 'Sant Vicenç H.',    't_viaje': 2, 'tasa_base': 6.0, 'ratio_bajada': 0.2},
    {'nombre': 'Cervelló',          't_viaje': 3, 'tasa_base': 8.0, 'ratio_bajada': 0.3},
    {'nombre': 'Vallirana',         't_viaje': 0, 'tasa_base': 10.0, 'ratio_bajada': 1.0}
]

def simular_linea_completa(tiempo_fin=720):
    env = simpy.Environment()
    
    paradas = []
    for conf in config_paradas:
        paradas.append({
            'nombre': conf['nombre'],
            'recurso': simpy.Resource(env, capacity=1),
            't_viaje': conf['t_viaje'],
            'tasa_base': conf['tasa_base'],
            'ratio_bajada': conf['ratio_bajada'],
            'cola': 0,
            'lst_bus_arr': 0,
            'total_pujats': 0,
            'total_rebutjats': 0
        })
        
    datos_intervalos = []
    datos_colas = {'Tiempos': [], 'Francesc Macià': [], 'Hospital-TV3': []}
    
    # Variable para controlar la OPCIÓN C (Estrategia de Holding)
    estat_linia = {'ultima_sortida_fm': 0}

    def monitor_colas():
        while True:
            datos_colas['Tiempos'].append(env.now)
            datos_colas['Francesc Macià'].append(paradas[0]['cola'])
            datos_colas['Hospital-TV3'].append(paradas[3]['cola'])
            yield env.timeout(1)

    # --- OPCIÓN A: Demanda Variable ---
    def gen_pasajeros(parada):
        while True:
            es_hora_punta = (0 <= env.now <= 120) or (360 <= env.now <= 480)
            multiplicador = 0.5 if es_hora_punta else 1.5
            tasa_actual = parada['tasa_base'] * multiplicador
            yield env.timeout(random.expovariate(1.0 / tasa_actual))
            parada['cola'] += 1

    # --- OPCIÓN B & C: Capacidad Finita y Holding ---
    def autobus(id_bus):
        pasajeros_a_bordo = 0
        
        while True:
            for parada in paradas:
                with parada['recurso'].request() as req:
                    yield req
                    
                    if parada['nombre'] == 'Francesc Macià':
                        hueco = env.now - parada['lst_bus_arr']
                        if env.now > 20: 
                            datos_intervalos.append((env.now, hueco))
                        parada['lst_bus_arr'] = env.now

                    # Opción B: Bajan y Suben pasajeros
                    bajan = int(pasajeros_a_bordo * parada['ratio_bajada'])
                    pasajeros_a_bordo -= bajan
                    
                    espacio_libre = CAPACITAT_MAXIMA - pasajeros_a_bordo
                    suben = min(parada['cola'], espacio_libre)
                    
                    parada['cola'] -= suben
                    pasajeros_a_bordo += suben
                    parada['total_pujats'] += suben
                    
                    if parada['cola'] > 0 and espacio_libre == suben:
                        parada['total_rebutjats'] += parada['cola']
                    
                    tiempo_parada = (bajan * 0.1) + (suben * 0.2)
                    yield env.timeout(tiempo_parada)
                    
                    # ----------------------------------------------------
                    # OPCIÓN C: ESTRATEGIA DE HOLDING (Regulación)
                    # ----------------------------------------------------
                    if parada['nombre'] == 'Francesc Macià':
                        temps_des_de_l_ultim = env.now - estat_linia['ultima_sortida_fm']
                        
                        # Si ha pasado menos del intervalo ideal, EL BUS SE ESPERA
                        if temps_des_de_l_ultim < INTERVAL_IDEAL:
                            temps_espera = INTERVAL_IDEAL - temps_des_de_l_ultim
                            yield env.timeout(temps_espera)
                        
                        # Guardamos la hora exacta en la que este bus arranca motores
                        estat_linia['ultima_sortida_fm'] = env.now
                
                # Viaje a la siguiente parada
                if parada['t_viaje'] > 0:
                    yield env.timeout(max(0, random.normalvariate(parada['t_viaje'], 0.5)))
            
            # Retorno en vacío
            pasajeros_a_bordo = 0
            yield env.timeout(30)

    for p in paradas:
        env.process(gen_pasajeros(p))

    def despachar_flota():
        for i in range(5):
            env.process(autobus(i+1))
            yield env.timeout(INTERVAL_IDEAL) 
            
    env.process(despachar_flota())
    env.process(monitor_colas())

    print("Simulant model GOD TIER (A + B + C)...")
    env.run(until=tiempo_fin)
    
    return datos_intervalos, datos_colas, paradas

# ==========================================
# EJECUCIÓN Y GRÁFICOS
# ==========================================
datos_intervalos, datos_colas, stats_paradas = simular_linea_completa(720)

print("\n" + "="*70)
print(f"📊 ESTADÍSTIQUES FINALS (Capacitat: 50 | Hores Punta | HOLDING)")
print("="*70)
total_pujats = 0
total_rebutjats = 0
for p in stats_paradas:
    print(f"Parada: {p['nombre']:<20} | Pujats: {p['total_pujats']:<5} | Rebutjats: {p['total_rebutjats']}")
    total_pujats += p['total_pujats']
    total_rebutjats += p['total_rebutjats']
print("-" * 70)
print(f"🚌 TOTAL PASSATGERS TRANSPORTATS: {total_pujats}")
print(f"❌ TOTAL PASSATGERS DEIXATS A TERRA: {total_rebutjats}")
print("="*70)

# ==========================================
# GENERACIÓN DE GRÁFICOS
# ==========================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

tiempos_int = [p[0] for p in datos_intervalos]
huecos = [p[1] for p in datos_intervalos]

ax1.plot(tiempos_int, huecos, linestyle='-', marker='o', color='blue', markersize=3, alpha=0.7)
ax1.axvspan(0, 120, color='red', alpha=0.1, label='Hora Punta (Matí)')
ax1.axvspan(360, 480, color='red', alpha=0.1, label='Hora Punta (Migdia)')
ax1.axhline(y=15, color='green', linestyle='--', label='Interval Ideal Mínim (15 min)')
ax1.set_title("Efecte Acordió Mitigat (Amb Holding): Interval d'Arribada a F. Macià", fontsize=14, fontweight='bold')
ax1.set_ylabel("Interval (minuts)", fontsize=12)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.set_ylim(bottom=0)

t_colas = datos_colas['Tiempos']
c_fm = datos_colas['Francesc Macià']
c_htv = datos_colas['Hospital-TV3']

ax2.plot(t_colas, c_fm, color='darkorange', linewidth=1.5, label='Cua a Francesc Macià')
ax2.plot(t_colas, c_htv, color='purple', linewidth=1.5, alpha=0.7, label='Cua a Hospital-TV3')
ax2.axvspan(0, 120, color='red', alpha=0.1)
ax2.axvspan(360, 480, color='red', alpha=0.1)
ax2.set_title("Ocupació de les Parades (Capacitat limitada a 50 places)", fontsize=14, fontweight='bold')
ax2.set_xlabel("Temps de simulació (minuts)", fontsize=12)
ax2.set_ylabel("Passatgers esperant", fontsize=12)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig('grafics_ABC_TotCombinat.png', dpi=300, bbox_inches='tight')
print("✅ Gràfics guardats com a 'grafics_ABC_TotCombinat.png'")

try:
    plt.show()
except:
    pass