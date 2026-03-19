import simpy
import random
import matplotlib.pyplot as plt

random.seed(42)

# ==========================================
# CONFIGURACIÓN DE LA LÍNEA Y PARADAS
# ==========================================
# tasa_base: Minutos promedio entre la llegada de cada pasajero (menor = más gente)
config_paradas = [
    {'nombre': 'Francesc Macià',    't_viaje': 3, 'tasa_base': 1.5}, # Mucha demanda
    {'nombre': 'Reina M. Cristina', 't_viaje': 2, 'tasa_base': 2.0},
    {'nombre': 'Zona Universitària','t_viaje': 3, 'tasa_base': 2.5},
    {'nombre': 'Hospital-TV3',      't_viaje': 5, 'tasa_base': 3.0},
    {'nombre': 'Sant Feliu',        't_viaje': 5, 'tasa_base': 4.0},
    {'nombre': 'Molins de Rei',     't_viaje': 3, 'tasa_base': 4.5},
    {'nombre': 'Sant Vicenç H.',    't_viaje': 2, 'tasa_base': 6.0},
    {'nombre': 'Cervelló',          't_viaje': 3, 'tasa_base': 8.0},
    {'nombre': 'Vallirana',         't_viaje': 0, 'tasa_base': 10.0} # Poca demanda, fin trayecto
]

# ==========================================
# MODELO DE SIMULACIÓN
# ==========================================
def simular_linea_completa(tiempo_fin=720): # Simulamos 12 horas (720 min)
    env = simpy.Environment()
    
    # Creamos las paradas dinámicamente
    paradas = []
    for conf in config_paradas:
        paradas.append({
            'nombre': conf['nombre'],
            'recurso': simpy.Resource(env, capacity=1),
            't_viaje': conf['t_viaje'],
            'tasa_base': conf['tasa_base'],
            'cola': 0,
            'lst_bus': 0
        })
        
    datos_grafico = []

    # --- Generador de Pasajeros con DEMANDA VARIABLE (Opción A) ---
    def gen_pasajeros(parada):
        while True:
            # Definimos Horas Punta: De 0 a 120 (mañana) y de 360 a 480 (mediodía)
            es_hora_punta = (0 <= env.now <= 120) or (360 <= env.now <= 480)
            
            # En hora punta, la tasa baja a la mitad (llega el doble de gente)
            # En hora valle, la tasa sube un 50% (llega menos gente)
            multiplicador = 0.5 if es_hora_punta else 1.5
            tasa_actual = parada['tasa_base'] * multiplicador
            
            yield env.timeout(random.expovariate(1.0 / tasa_actual))
            parada['cola'] += 1

    # --- Ruta de los 5 Autobuses ---
    def autobus(id_bus):
        while True:
            for i, parada in enumerate(paradas):
                with parada['recurso'].request() as req:
                    yield req
                    
                    # Registramos el bus bunching SOLO en Francesc Macià para tener un gráfico claro
                    if parada['nombre'] == 'Francesc Macià':
                        hueco = env.now - parada['lst_bus']
                        if env.now > 20: # Ignoramos el arranque inicial
                            datos_grafico.append((env.now, hueco))
                        parada['lst_bus'] = env.now

                    # Embarque: asumimos 0.2 minutos (12 seg) por persona
                    tiempo_embarque = parada['cola'] * 0.2
                    parada['cola'] = 0
                    yield env.timeout(tiempo_embarque)
                
                # Viaje a la siguiente parada (con pequeña variación de tráfico)
                if parada['t_viaje'] > 0:
                    yield env.timeout(max(0, random.normalvariate(parada['t_viaje'], 0.5)))
            
            # Al llegar a Vallirana, el bus hace un viaje de vuelta a Barcelona vacío (30 mins)
            yield env.timeout(30)

    # --- Inicialización ---
    for p in paradas:
        env.process(gen_pasajeros(p))

    # Lanzamos los 5 autobuses separados por 15 minutos iniciales
    def despachar_flota():
        for i in range(5):
            env.process(autobus(i+1))
            yield env.timeout(15)
            
    env.process(despachar_flota())

    print("Simulando línea completa con Demanda Variable...")
    env.run(until=tiempo_fin)
    return datos_grafico

# ==========================================
# EJECUCIÓN Y GRÁFICO
# ==========================================
datos = simular_linea_completa(720) # 12 horas de servicio

tiempos = [p[0] for p in datos]
huecos = [p[1] for p in datos]

plt.figure(figsize=(12, 6))
plt.plot(tiempos, huecos, linestyle='-', marker='o', color='blue', markersize=3, alpha=0.7)

# Pintamos franjas de fondo para destacar las HORAS PUNTA
plt.axvspan(0, 120, color='red', alpha=0.1, label='Hora Punta (Matí)')
plt.axvspan(360, 480, color='red', alpha=0.1, label='Hora Punta (Migdia)')

plt.title("Efecte Acordió (Demanda Variable) - 5 Autobusos, 9 Parades", fontsize=14)
plt.xlabel("Temps de simulació (minuts)", fontsize=12)
plt.ylabel("Interval entre autobusos a F. Macià (minuts)", fontsize=12)
plt.axhline(y=15, color='green', linestyle='--', label='Interval Ideal (15 min)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.ylim(bottom=0)
plt.tight_layout()
plt.show()