import simpy
import random

# Variables globales: Contadores de pasajeros en cada parada (como X$GFM, X$GHT...)
passengers = {'FM': 0, 'HTV': 0, 'VAL': 0}

# 1. FUNCIÓN DE TIEMPO DE EMBARQUE (Movilidad reducida)
def get_boarding_time():
    # 90% tarda 3s, 10% tarda 15s (Igual que FN$TSUB)
    return random.choices([3, 15], weights=[0.9, 0.1])[0]

# 2. GENERADORES DE PASAJEROS (Independientes de los buses)
def passenger_generator(env, stop_name, mean_interval):
    while True:
        # Distribución exponencial (Igual que FN$EXP)
        time_to_next = random.expovariate(1.0 / mean_interval)
        yield env.timeout(time_to_next)
        passengers[stop_name] += 1 # Llega un pasajero a la parada

# 3. RUTINA DEL AUTOBÚS (La transacción principal)
def bus(env, bus_id):
    while True:
        # --- PARADA 1: FM ---
        num_pas = passengers['FM']  # Miramos cuántos hay
        passengers['FM'] = 0        # Vaciamos la parada
        for _ in range(num_pas):    # Bucle de subida de pasajeros
            yield env.timeout(get_boarding_time())
        
        # Trayecto FM -> HTV (5 ± 1 unidades de tiempo)
        yield env.timeout(random.uniform(4, 6))

        # --- PARADA 2: HTV ---
        num_pas = passengers['HTV']
        passengers['HTV'] = 0
        for _ in range(num_pas):
            yield env.timeout(get_boarding_time())
        
        # Trayecto HTV -> VAL (10 ± 2 unidades de tiempo)
        yield env.timeout(random.uniform(8, 12))

        # --- PARADA 3: VAL ---
        num_pas = passengers['VAL']
        passengers['VAL'] = 0
        for _ in range(num_pas):
            yield env.timeout(get_boarding_time())
        
        # Vuelve a FM (trayecto instantáneo según la lógica que teníamos)

# 4. LANZADOR DE BUSES (Para que no salgan a la vez)
def bus_launcher(env):
    env.process(bus(env, 1))      # Sale el Bus 1 en t=0
    yield env.timeout(10)         # Esperamos 10 unidades de tiempo
    env.process(bus(env, 2))      # Sale el Bus 2 en t=10

# ==========================================
# CONFIGURACIÓN Y EJECUCIÓN
# ==========================================
env = simpy.Environment()

# Arrancamos los generadores de pasajeros (medias de 20, 18 y 16)
env.process(passenger_generator(env, 'FM', 20))
env.process(passenger_generator(env, 'HTV', 18))
env.process(passenger_generator(env, 'VAL', 16))

# Arrancamos los buses
env.process(bus_launcher(env))

# Ejecutamos la simulación durante 1000 unidades de tiempo (Igual que el GENERATE 1000)
print("Iniciando simulación...")
env.run(until=1000)

print("Simulación terminada.")
print(f"Pasajeros frustrados esperando al final de la jornada: {passengers}")