from flask import Flask, jsonify
from threading import Thread
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent, CarAgent, AmbulanceAgent, ParkingCarAgent
from models import IntersectionModel

from map import optionMap, garages, Semaphores
from unity_mapping import mapping

# Crear la aplicación Flask
app = Flask(__name__)


# Definir la representación de los agentes
def intersectionPortrayal(agent):
    if agent is None:
        return

    portrayal = {"Filled": "true"}

    if isinstance(agent, BuildingAgent):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
        portrayal["Color"] = "#808080"  # Grey for buildings
        portrayal["Layer"] = 1

    elif isinstance(agent, TrafficLightAgent):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.6
        portrayal["h"] = 0.6
        if agent.state == "green":
            portrayal["Color"] = "green"
        elif agent.state == "red":
            portrayal["Color"] = "red"
        else:
            portrayal["Color"] = "yellow"
        portrayal["Layer"] = 2

    elif isinstance(agent, ParkingSpotAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.3
        portrayal["Color"] = "#0000FF"  # Blue for parking spots
        portrayal["Layer"] = 3

    elif isinstance(agent, CarAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Color"] = "black" if agent.state == "happy" else "red"
        portrayal["Layer"] = 3

    elif isinstance(agent, AmbulanceAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Color"] = "purple"
        portrayal["Layer"] = 3

    elif isinstance(agent, ParkingCarAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Color"] = "brown" if agent.state == "happy" else "yellow"
        portrayal["Layer"] = 3

    return portrayal


"""# Instancia del modelo
model = IntersectionModel(
    size=24,
    option_map=optionMap,
    garages=garages,
    semaphores=Semaphores,
    num_cars=20  # Especificar número de coches
)"""


# Configuración de MESA
grid = CanvasGrid(intersectionPortrayal, 24, 24, 500, 500)

emotion_chart = ChartModule(
    [
        {"Label": "HappyCars", "Color": "Blue"},
        {"Label": "AngryCars", "Color": "Red"}
    ],
    data_collector_name='datacollector'
)

server = ModularServer(
    IntersectionModel,
    [grid, emotion_chart],
    "Intersection Simulation",
    {
        "size": 24,
        "option_map": optionMap,
        "garages": garages,
        "semaphores": Semaphores,
        "num_cars": 20
    }
)

server.port = 8521

model: IntersectionModel = server.model


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

# Bloque principal
if __name__ == "__main__":
    # Iniciar el servidor Flask en un hilo separado
    flask_thread = Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()

    print("Starting MESA server...")
    # Iniciar la simulación MESA
    server.launch()
    model = server.model
