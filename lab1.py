import simpy
import random
import matplotlib.pyplot as plt

def simulacion_con_graficos(tiempo_total=1000):
    env = simpy.Environment()
    passengers = {'FM': 0, 'HTV': 0, 'VAL': 0}
    
    parada_FM = simpy.Resource(env, capacity=1)
    parada_HTV = simpy.Resource(env, capacity=1)
    parada_VAL = simpy.Resource(env, capacity=1)
    
    # Listas para guardar datos para las gráficas
    llegadas_FM = []
    intervalos_FM = []
    cues_FM = []

    def get_boarding_time():
        return random.choices([3, 15], weights=[0.9, 0.1])[0]

    def passenger_generator(env, stop_name, mean_interval):
        while True:
            yield env.timeout(random.expovariate(1.0 / mean_interval))
            passengers[stop_name] += 1

    def bus(env, bus_id):
        while True:
            # --- PARADA 1: FM (Donde tomamos las medidas) ---
            llegadas_FM.append(env.now)
            if len(llegadas_FM) > 1:
                intervalos_FM.append(llegadas_FM[-1] - llegadas_FM[-2])
            
            with parada_FM.request() as req:
                yield req
                num_pas = passengers['FM']
                cues_FM.append(num_pas) # Guardamos la cola para la gráfica
                passengers['FM'] = 0
                for _ in range(num_pas):
                    yield env.timeout(get_boarding_time())
            yield env.timeout(random.uniform(4, 6))

            # --- PARADA 2: HTV ---
            with parada_HTV.request() as req:
                yield req
                num_pas = passengers['HTV']
                passengers['HTV'] = 0
                for _ in range(num_pas):
                    yield env.timeout(get_boarding_time())
            yield env.timeout(random.uniform(8, 12))

            # --- PARADA 3: VAL ---
            with parada_VAL.request() as req:
                yield req
                num_pas = passengers['VAL']
                passengers['VAL'] = 0
                for _ in range(num_pas):
                    yield env.timeout(get_boarding_time())

    def bus_launcher(env):
        env.process(bus(env, 1))      
        yield env.timeout(10) # Separación ideal de 10 min
        env.process(bus(env, 2))      

    env.process(passenger_generator(env, 'FM', 20))
    env.process(passenger_generator(env, 'HTV', 18))
    env.process(passenger_generator(env, 'VAL', 16))
    env.process(bus_launcher(env))
    
    env.run(until=tiempo_total)
    
    return llegadas_FM, intervalos_FM, cues_FM

# Ejecutamos la simulación
tiempos_llegada, intervalos, colas = simulacion_con_graficos(tiempo_total=1000)

# ==========================================
# GENERACIÓN DE LAS GRÁFICAS (MATPLOTLIB)
# ==========================================
# Creamos una figura con dos subgráficos (1 fila, 2 columnas)
plt.figure(figsize=(14, 5))

# --- GRÁFICO 1: Intervalos entre autobuses ---
plt.subplot(1, 2, 1)
# El eje X es el tiempo de llegada (quitamos el primer dato porque no tiene intervalo previo)
plt.plot(tiempos_llegada[1:], intervalos, marker='o', linestyle='-', color='b')
# Dibujamos una línea roja que marca el "Mundo Ideal" (10 minutos)
plt.axhline(y=10, color='r', linestyle='--', label='Intervalo Ideal (10 min)')
plt.title('Efecto Acordeón: Intervalo entre Autobuses (Parada FM)')
plt.xlabel('Tiempo de Simulación (minutos)')
plt.ylabel('Intervalo respecto al bus anterior (minutos)')
plt.legend()
plt.grid(True, alpha=0.3)

# --- GRÁFICO 2: Ocupación/Colas en la parada ---
plt.subplot(1, 2, 2)
plt.plot(tiempos_llegada, colas, marker='s', linestyle='-', color='g')
plt.title('Evolución de la Cola de Pasajeros (Parada FM)')
plt.xlabel('Tiempo de Simulación (minutos)')
plt.ylabel('Pasajeros esperando')
plt.grid(True, alpha=0.3)

# Mostramos las gráficas por pantalla
plt.tight_layout()
plt.show()