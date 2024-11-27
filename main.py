from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent, CarAgent, ParkingCarAgent, AmbulanceAgent
from map import optionMap, garages, Semaphores, startList

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


"""
# Instantiate the model with the size and the maps
model = IntersectionModel(
    size=24,
    option_map=optionMap,
    garages=garages,
    semaphores=Semaphores
)
"""


# Set up the visualization
grid = CanvasGrid(intersectionPortrayal, 24, 24, 500, 500)

model_params = {
    "size": 24,
    "option_map": optionMap,
    "garages": garages,
    "semaphores": Semaphores,
    "num_cars": 20,  # Specify the number of cars
}
emotion_chart = ChartModule(
    [
        {"Label": "HappyCars", "Color": "Blue"},
        {"Label": "AngryCars", "Color": "Red"}
    ],
    data_collector_name='datacollector'
)

# ModularServer setup
server = ModularServer(
    IntersectionModel,
    [grid, emotion_chart],
    "Intersection Simulation",
    model_params
)


server.port = 8521
server.launch()
