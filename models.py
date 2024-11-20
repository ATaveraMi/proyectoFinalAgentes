from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random
from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent
from map import optionMap, startList, endList, Semaphores


class IntersectionModel(Model):
    def __init__(self, size, option_map, garages, semaphores):
        self.schedule = SimultaneousActivation(self)
        self.grid = MultiGrid(size, size, torus=False)
        self.running = True
        self.current_id = 0  # Initialize current_id for unique agent IDs
        
        self.option_map = option_map
        self.garages = garages
        self.semaphores = semaphores

        # Initialize agents
        self.create_cells()
        self.create_garages()
        self.create_traffic_lights()
        self.create_buildings(size)

    def create_cells(self):
        """Populate the grid based on the optionMap."""
        for pos, options in self.option_map.items():
            # Represent the cell as open space or a road
            pass  # Optionally, implement a cell agent if needed

    def create_garages(self):
        """Place parking spots (garages) in the grid."""
        for pos in self.garages:
            garage_agent = ParkingSpotAgent(self.next_id(), self)
            self.schedule.add(garage_agent)
            self.grid.place_agent(garage_agent, pos)

    def create_traffic_lights(self):
        """Place traffic lights in the grid."""
        for pos, state in self.semaphores:
            traffic_light_agent = TrafficLightAgent(self.next_id(), self, pos, state)
            self.schedule.add(traffic_light_agent)
            self.grid.place_agent(traffic_light_agent, pos)

    def create_buildings(self, size):
        """Fill in the rest of the grid with buildings."""
        for x in range(size):
            for y in range(size):
                pos = (x, y)
                if pos not in self.option_map and pos not in self.garages and pos not in [s[0] for s in self.semaphores]:
                    building_agent = BuildingAgent(self.next_id(), self)
                    self.schedule.add(building_agent)
                    self.grid.place_agent(building_agent, pos)
