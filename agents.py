from mesa import Agent
import random
from mesa.space import MultiGrid
from map import endList
class BuildingAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_building = True

    def step(self):
        pass


class TrafficLightAgent(Agent):
    def __init__(self, unique_id, model, pos, state):
        super().__init__(unique_id, model)
        self.pos = pos
        self.state = state  # Initial state: "red", "green", or "yellow"
        

        self.timer = 5 if state == "green" else 7  # Set initial timer based on initial state

    def step(self):
        pass  

class ParkingSpotAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_occupied = False  # Initially, no car is in the spot

    def step(self):
        # Implement behavior for cars parking/unparking if needed
        pass
