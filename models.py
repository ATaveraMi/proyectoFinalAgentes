from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random
from agents import BuildingAgent, TrafficLightAgent, ParkingSpotAgent, CarAgent, ParkingCarAgent, WrecklessAgent
from dijkstra import dijkstra, create_maximal_graph

from map import endList, startList, optionMap

class IntersectionModel(Model):
    def __init__(self, size, option_map, garages, semaphores, num_cars=10):
        super().__init__()
        self.size = size
        self.traffic_lights = []  
        self.schedule = SimultaneousActivation(self)
        self.grid = MultiGrid(size, size, torus=False)
        self.running = True
        self.current_id = 0  # Initialize current_id for unique agent IDs
        self.parked_cars = 0
        self.used_starts = set()
        
        self.remaining_slots = len(garages)
        self.option_map = option_map
        self.garages = garages
        self.semaphores = semaphores
        self.num_cars = num_cars

        self.startList = startList.copy()
        self.endList = self.garages.copy()

        # Initialize graph for A* algorithm
        self.G = create_maximal_graph(self.option_map)

        # Initialize agents
        self.create_garages()
        self.create_traffic_lights()
        self.create_buildings(size)
        self.create_cars()

    """
    Código agregado para darle pasos a los coches.
    - Orla
    """
    def step(self):
        self.schedule.step()

    def initialize_graph(self):
        return create_maximal_graph(self.option_map)
    
    def reset(self):
        self.startList = startList.copy()
        self.endList = self.garages.copy()

    def create_traffic_lights(self):
        for pos, state in self.semaphores:
            if self.grid.is_cell_empty(pos):
                traffic_light_agent = TrafficLightAgent(self.next_id(), self, pos, state)
                self.schedule.add(traffic_light_agent)
                self.grid.place_agent(traffic_light_agent, pos)
                self.traffic_lights.append(traffic_light_agent)  # Add to the list
            else:
                print(f"Position {pos} is already occupied. Skipping.")

        # Set the first traffic light to green
        if self.traffic_lights:
            self.light_index = 0
            first_light = self.traffic_lights[self.light_index]
            first_light.state = "green"
            first_light.timer = 6  # Green lasts 6 seconds
            print(f"Traffic light at {first_light.pos} initialized to green.")

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
        
    def create_cars(self):
        """Create agents with a mix of wanderers and parking cars."""
        num_parking_cars = 0  # Track the number of ParkingCarAgents created

        # Get all possible positions from optionMap
        available_positions = list(self.option_map.keys())

        for _ in range(self.num_cars):
            # Select a random starting position
            if not available_positions:
                print("No available positions remaining in optionMap.")
                return
            
            starting_pos = random.choice(available_positions)

            # Ensure the position is not occupied
            cell_contents = self.grid.get_cell_list_contents([starting_pos])
            if any(isinstance(agent, CarAgent) or isinstance(agent, ParkingCarAgent) for agent in cell_contents):
                continue  # Skip to the next iteration if the position is occupied

            # Decide the type of car (40% chance for ParkingCarAgent)
            if random.random() < 0.1:  # 10% chance to create a WrecklessAgent
                car_agent = WrecklessAgent(
                    unique_id=self.next_id(),
                    model=self
                )
                print(f"Created WrecklessAgent {car_agent.unique_id} at {starting_pos}.")
            elif random.random() < 0.4 and num_parking_cars < len(self.endList):
                # Create a ParkingCarAgent
                if not self.endList:  # Ensure there are target positions left
                    print("No available parking slots remaining.")
                    continue

                target_pos = random.choice(self.endList)
                self.endList.remove(target_pos)

                # Compute the shortest path using Dijkstra
                path = dijkstra(self.G, starting_pos, target_pos)
                if not path:
                    print(f"No path found from {starting_pos} to {target_pos}. Skipping this car.")
                    continue

                car_agent = ParkingCarAgent(
                    unique_id=self.next_id(),
                    model=self,
                    starting_pos=starting_pos,
                    target_pos=target_pos,
                    path=path,
                )
                num_parking_cars += 1
                print(f"Created ParkingCarAgent {car_agent.unique_id} at {starting_pos} targeting {target_pos}.")
            else:
                # Create a WandererAgent
                car_agent = CarAgent(
                    unique_id=self.next_id(),
                    model=self,
                )
                print(f"Created CarAgent {car_agent.unique_id} at {starting_pos} wandering freely.")

            # Add the car agent to the schedule and place it on the grid
            self.schedule.add(car_agent)
            self.grid.place_agent(car_agent, starting_pos)

            # Remove the position from available_positions to avoid reuse
            available_positions.remove(starting_pos)
