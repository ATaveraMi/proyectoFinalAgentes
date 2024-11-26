from flask import Flask, jsonify
from threading import Thread
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent, CarAgent
from models import IntersectionModel
from map import optionMap, garages, Semaphores

# Crear la aplicación Flask
app = Flask(__name__)

# Instancia del modelo
model = IntersectionModel(
    size=24,
    option_map=optionMap,
    garages=garages,
    semaphores=Semaphores
)


@app.route('/traffic_data', methods=['GET'])
def get_traffic_data():

    model.step()

    traffic_lights = model.get_traffic_light_states()
    cars = model.get_car_states()
    return jsonify({
        'traffic_lights': traffic_lights,
        'cars': cars
    })


# Hilo para ejecutar Flask
def run_flask():
    print("Starting Flask server...")
    app.run(port=5000, debug=False, use_reloader=False)

# Configurar la visualización de MESA
def intersectionPortrayal(agent):
    if agent is None:
        return

    portrayal = {"Filled": "true"}

    if isinstance(agent, BuildingAgent):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
        portrayal["Color"] = "#808080"  # Grey for buildings
        portrayal["Layer"] = 1  # Layer para edificios

    elif isinstance(agent, TrafficLightAgent):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.6
        portrayal["h"] = 0.6
        portrayal["Color"] = (
            "green" if agent.state == "green" else
            "red" if agent.state == "red" else
            "yellow"
        )
        portrayal["Layer"] = 2  # Layer para semáforos

    elif isinstance(agent, ParkingSpotAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.3
        portrayal["Color"] = "#0000FF"  # Blue for parking spots
        portrayal["Layer"] = 3  # Layer para estacionamientos

    elif isinstance(agent, CarAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Color"] = "black" if agent.state == "happy" else "red"
        portrayal["Layer"] = 3  # Layer para coches

    else:
        portrayal["Layer"] = 0  # Fallback layer

    return portrayal

grid = CanvasGrid(intersectionPortrayal, 24, 24, 500, 500)

server = ModularServer(
    IntersectionModel,
    [grid],
    "Intersection Simulation",
    {
        "size": 24,
        "option_map": optionMap,
        "garages": garages,
        "semaphores": Semaphores,
        "num_cars": 4
    }
)

server.port = 8521

# Bloque principal
if __name__ == "__main__":
    # Iniciar el servidor Flask en un hilo separado
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Starting MESA server...")
    # Iniciar la simulación MESA
    server.launch()
