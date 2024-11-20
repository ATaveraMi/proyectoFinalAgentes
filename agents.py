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
