import simpy
import random
import statistics
import matplotlib.pyplot as plt

# Configuramos la semilla aleatoria para que sea reproducible
random.seed(42)

def ejecutar_simulacion(tiempo_fin=1000):
    env = simpy.Environment()

    # Variables de estado (Pasajeros esperando)
    estado = {'gfm': 0, 'ght': 0, 'gva': 0, 'lstfm': 0}
    
    # Diccionario para guardar nuestras estadísticas
    stats = {
        'FM_entradas': 0, 'FM_tiempo_total': 0,
        'HT_entradas': 0, 'HT_tiempo_total': 0,
        'VA_entradas': 0, 'VA_tiempo_total': 0,
    }
    
    # Lista para guardar las coordenadas del gráfico: (Tiempo, Hueco)
    datos_grafico = []

    # Recursos (Paradas)
    sfm = simpy.Resource(env, capacity=1)
    sht = simpy.Resource(env, capacity=1)
    sva = simpy.Resource(env, capacity=1)

    # --- Generadores de pasajeros ---
    def gen_pasajeros_fm():
        while True:
            yield env.timeout(random.uniform(19, 21)) # GENERATE 20,1
            estado['gfm'] += 1

    def gen_pasajeros_ht():
        while True:
            yield env.timeout(random.uniform(9, 27))  # GENERATE 18,9
            estado['ght'] += 1

    def gen_pasajeros_va():
        while True:
            yield env.timeout(random.uniform(14, 18)) # GENERATE 16,2
            estado['gva'] += 1

    # --- Ruta del autobús ---
    def autobus(id_bus):
        while True:
            # PARADA 1: Francesc Macià
            with sfm.request() as req:
                yield req
                
                # Calculamos el hueco (tiempo desde que pasó CUALQUIER bus anterior)
                hueco = env.now - estado['lstfm']
                
                # AHORA SÍ: Guardamos el dato para TODOS los autobuses, igual que en GPSS
                if env.now > 0:
                    datos_grafico.append((env.now, hueco))
                
                tiempo_embarque = estado['gfm']
                estado['lstfm'] = env.now
                estado['gfm'] = 0
                
                yield env.timeout(tiempo_embarque)
                stats['FM_entradas'] += 1
                stats['FM_tiempo_total'] += tiempo_embarque

            yield env.timeout(5) # Viaje a HTV

            # PARADA 2: Hospital-TV3
            with sht.request() as req:
                yield req
                tiempo_embarque = estado['ght']
                estado['ght'] = 0
                yield env.timeout(tiempo_embarque)
                stats['HT_entradas'] += 1
                stats['HT_tiempo_total'] += tiempo_embarque

            yield env.timeout(10) # Viaje a VAL

            # PARADA 3: Vallirana
            with sva.request() as req:
                yield req
                tiempo_embarque = estado['gva']
                estado['gva'] = 0
                yield env.timeout(tiempo_embarque)
                stats['VA_entradas'] += 1
                stats['VA_tiempo_total'] += tiempo_embarque
            
            # GOTO QFM (Regreso instantáneo)

    # --- Generador de Autobuses ---
    def gen_buses():
        env.process(autobus(1))
        yield env.timeout(10) # Separación inicial
        env.process(autobus(2))

    # Arrancamos procesos
    env.process(gen_pasajeros_fm())
    env.process(gen_pasajeros_ht())
    env.process(gen_pasajeros_va())
    env.process(gen_buses())

    env.run(until=tiempo_fin)
    
    # Calcular métricas finales de esta simulación
    metrics = {
        'FM_utilizacion': (stats['FM_tiempo_total'] / tiempo_fin) * 100,
        'HT_utilizacion': (stats['HT_tiempo_total'] / tiempo_fin) * 100,
        'VA_utilizacion': (stats['VA_tiempo_total'] / tiempo_fin) * 100,
        'FM_avg_time': stats['FM_tiempo_total'] / stats['FM_entradas'] if stats['FM_entradas'] > 0 else 0,
        'HT_avg_time': stats['HT_tiempo_total'] / stats['HT_entradas'] if stats['HT_entradas'] > 0 else 0,
        'VA_avg_time': stats['VA_tiempo_total'] / stats['VA_entradas'] if stats['VA_entradas'] > 0 else 0,
        'FM_entradas': stats['FM_entradas'],
        'HT_entradas': stats['HT_entradas'],
        'VA_entradas': stats['VA_entradas']
    }
    return metrics, datos_grafico

# ==========================================
# 1. EJECUCIÓN MÚLTIPLE (Estadísticas N=10)
# ==========================================
print("Ejecutando simulación 10 veces para Validacion Cruzada...")
resultados_metricas = []
datos_grafico_ejemplo = None

for i in range(10):
    metricas, grafico = ejecutar_simulacion()
    resultados_metricas.append(metricas)
    if i == 0:
        datos_grafico_ejemplo = grafico

promedios = {k: statistics.mean([res[k] for res in resultados_metricas]) for k in resultados_metricas[0].keys()}

print("\n=== TABLA DE COMPARACIÓN (PYTHON vs GPSS) ===")
print("Metrica\t\t\tPython (Media N=10)\tGPSS (Tu reporte)")
print("-" * 65)
print(f"Entradas FM\t\t{promedios['FM_entradas']:.1f}\t\t\t114")
print(f"Utilización FM (%)\t{promedios['FM_utilizacion']:.2f}%\t\t\t5.00%")
print(f"Tiempo Medio FM\t\t{promedios['FM_avg_time']:.2f}\t\t\t0.44")
print("-" * 65)
print(f"Entradas HT\t\t{promedios['HT_entradas']:.1f}\t\t\t112")
print(f"Utilización HT (%)\t{promedios['HT_utilizacion']:.2f}%\t\t\t5.40%")
print(f"Tiempo Medio HT\t\t{promedios['HT_avg_time']:.2f}\t\t\t0.48")
print("-" * 65)
print(f"Entradas VA\t\t{promedios['VA_entradas']:.1f}\t\t\t112")
print(f"Utilización VA (%)\t{promedios['VA_utilizacion']:.2f}%\t\t\t6.30%")
print(f"Tiempo Medio VA\t\t{promedios['VA_avg_time']:.2f}\t\t\t0.56")

# ==========================================
# 2. GENERACIÓN DEL GRÁFICO (Bus Bunching)
# ==========================================
print("\nGenerando gráfico del Efecto Acordeón...")

tiempos = [punto[0] for punto in datos_grafico_ejemplo]
huecos = [punto[1] for punto in datos_grafico_ejemplo]

plt.figure(figsize=(10, 5))

# Usamos línea roja más fina para simular el estilo de tu GPSS
plt.plot(tiempos, huecos, linestyle='-', color='red', linewidth=0.8)

plt.title("Evolució de l'Interval entre Autobusos a la Parada FM", fontsize=14)
plt.xlabel("Temps de simulació (minuts)", fontsize=12)
plt.ylabel("Interval (minuts)", fontsize=12)

plt.grid(True, linestyle='--', alpha=0.7)
plt.ylim(bottom=0)

plt.tight_layout()
plt.show()