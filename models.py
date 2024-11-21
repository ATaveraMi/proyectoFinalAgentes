from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random
from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent, CarAgent
from map import optionMap, endList, Semaphores
from aStar import astarComplete, manhattan_distance, create_maximal_graph


class IntersectionModel(Model):
    def __init__(self, size, option_map, garages, semaphores, num_cars=10):
        super().__init__()
        self.size = size
        self.schedule = SimultaneousActivation(self)
        self.grid = MultiGrid(size, size, torus=False)
        self.running = True
        self.current_id = 0  # Initialize current_id for unique agent IDs
        
        self.option_map = option_map
        self.garages = garages
        self.semaphores = semaphores
        self.num_cars = num_cars

        # Initialize graph for A* algorithm
        self.G = create_maximal_graph(optionMap)

        # Initialize agents
        self.create_cells()
        self.create_garages()
        self.create_traffic_lights()
        self.create_buildings(size)
        self.create_cars()

    def initialize_graph(self):
        """Create the graph for the A* algorithm based on the optionMap."""
        return create_maximal_graph(self.option_map)




    def create_cells(self):
        """Populate the grid based on the optionMap."""
        for pos, options in self.option_map.items():
            # Represent the cell as open space or a road
            pass  # Optionally, implement a cell agent if needed
    def create_buildings(self, size):
        """Fill in the rest of the grid with buildings."""
        for x in range(size):
            for y in range(size):
                pos = (x, y)
                if (
                    pos not in self.option_map
                    and pos not in self.garages
                    and pos not in [s[0] for s in self.semaphores]
                ):
                    building_agent = BuildingAgent(self.next_id(), self)
                    self.schedule.add(building_agent)
                    self.grid.place_agent(building_agent, pos)


    def create_garages(self):
        """Place parking spots (garages) in the grid."""
        for pos in self.garages:
            garage_agent = ParkingSpotAgent(self.next_id(), self)
            self.schedule.add(garage_agent)
            self.grid.place_agent(garage_agent, pos)

    def create_traffic_lights(self):
        for pos, state in self.semaphores:
            if self.grid.is_cell_empty(pos):
                traffic_light_agent = TrafficLightAgent(self.next_id(), self, pos, state)
                self.schedule.add(traffic_light_agent)
                self.grid.place_agent(traffic_light_agent, pos)
            else:
                print(f"Position {pos} is already occupied. Skipping.")

    def create_cars(self):
        max_retries = 50
        for _ in range(self.num_cars):
            retries = 0
            while retries < max_retries:
                if not endList:  # Stop if no more target positions
                    print("No available target positions remaining.")
                    return

                x = self.random.randrange(self.size)
                y = self.random.randrange(self.size)
                starting_pos = (x, y)

                if self.grid.is_cell_empty(starting_pos):
                    target_pos = self.random.choice(endList)

                    path = astarComplete(self.G, starting_pos, target_pos, manhattan_distance)

                    if path:
                        car_agent = CarAgent(
                            unique_id=self.next_id(),
                            model=self,
                            starting_pos=starting_pos,
                            target_pos=target_pos,
                            path=path,
                        )
                        self.schedule.add(car_agent)
                        self.grid.place_agent(car_agent, starting_pos)
                       
                        print(f"Placed car {car_agent.unique_id} at {starting_pos} targeting {target_pos}")
                        break
                    else:
                        print(f"No path found from {starting_pos} to {target_pos}. Retrying.")
                retries += 1

            if retries == max_retries:
                print(f"Failed to place a car after {max_retries} retries. Skipping.")
