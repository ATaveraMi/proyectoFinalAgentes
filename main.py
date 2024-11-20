from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent
from map import optionMap, garages, Semaphores
from models import IntersectionModel
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
import random

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

    return portrayal

# Función para reflejar las posiciones Y
def mirrored_portrayal(agent):
    """
    Aplica un reflejo sobre la arista inferior del grid.
    """
    portrayal = intersectionPortrayal(agent)
    if portrayal is not None:
        # Obtener la posición del agente
        x, y = agent.pos
        # Reflejar la posición Y
        portrayal["x"] = x
        portrayal["y"] = 24 - y - 1  # Cambiar aquí 24 por el tamaño del grid si es dinámico
    return portrayal

# Crear el grid con la función de reflejo
grid = CanvasGrid(mirrored_portrayal, 24, 24, 500, 500)

# Configuración del servidor
server = ModularServer(
    IntersectionModel,
    [grid],
    "Intersection Simulation (Mirrored)",
    {"size": 24, "option_map": optionMap, "garages": garages, "semaphores": Semaphores}
)

server.port = 8521
server.launch()

