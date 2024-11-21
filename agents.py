from mesa import Agent
import random
from mesa.space import MultiGrid
from aStar import astarComplete, manhattan_distance
from map import endList, optionMap
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
    
class CarAgent(Agent):
    def __init__(self, unique_id, model, starting_pos, target_pos, path, agent_type="neutral"):
        super().__init__(unique_id, model)
        self.starting_pos = starting_pos
        self.target_pos = target_pos
        self.path = path
        self.state = "happy"
        self.happiness = 100
        self.reached_goal = False
        self.jammedCounter = 0
        self.agent_type = agent_type  # "cooperative", "competitive", "neutral"
        self.last_negotiation = None
        self.reward_matrix = {
            ("Yield", "Yield"): (5, 5),
            ("Yield", "Advance"): (2, 8),
            ("Advance", "Yield"): (8, 2),
            ("Advance", "Advance"): (3, 3)
        }

    def recalculateNewPath(self):
        # Recalculate a new path if car is jammed
        new_target_pos = random.choice(endList)
        while new_target_pos == self.target_pos:
            new_target_pos = random.choice(endList)
        self.target_pos = new_target_pos
        self.path = astarComplete(self.model.G, self.pos, self.target_pos, manhattan_distance)
        self.jammedCounter = 0


    def negotiate(self, other_agent):
        # Determine the negotiation outcome based on agent types
        if self.agent_type == "competitive" and other_agent.agent_type == "competitive":
            my_action, other_reward = "Advance", "Advance"
        elif self.agent_type == "cooperative":
            my_action, other_reward = "Yield", "Advance"
        elif other_agent.agent_type == "cooperative":
            my_action, other_reward = "Advance", "Yield"
        else:
            my_action, other_reward = "Yield", "Yield"
        
        # Determine rewards (for potential future use)
        my_reward, other_reward = self.reward_matrix[(my_action, other_reward)]

        # Set the last_negotiation attribute based on the outcome
        if my_action == "Yield" and other_reward == "Yield":
            self.last_negotiation = "Yield"
        elif my_action == "Advance" and other_reward == "Advance":
            self.last_negotiation = "Stalemate"
        else:
            self.last_negotiation = "Advance" if my_action == "Advance" else "Yield"
        
        return my_action, my_reward


    def communicate_with_neighbors(self):
        # Decentralized communication with nearby agents
        nearby_agents = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
        messages = []
        for agent in nearby_agents:
            if isinstance(agent, CarAgent) and agent != self:
                messages.append({
                    "agent_id": agent.unique_id,
                    "position": agent.pos,
                    "intention": "moving" if agent.path else "waiting"
                })
        return messages

    def move(self):
        if self.pos == self.target_pos:
            print(f"Car {self.unique_id} has reached its destination at {self.pos} and will be removed.")
            self.model.grid.remove_agent(self)  # Remove the car from the grid
            self.model.schedule.remove(self)    # Remove the car from the schedule
            self.reached_goal = True
            return

        # Check if the car has already reached its destination or if the path is empty
        if not self.path:
            self.reached_goal = True
            print(f"Car {self.unique_id} has reached its destination or has an empty path.")
            return

        # Check if the car is jammed and needs to recalculate its path
        if self.jammedCounter >= 5:
            self.happiness -= 20
            print(f"Car {self.unique_id} recalculating path due to jammed counter at {self.jammedCounter}")
            self.recalculateNewPath()

            # Update state based on happiness level
            self.state = "angry" if self.happiness < 60 else "happy"

            if not self.path:
                self.reached_goal = True
                print(f"Car {self.unique_id} has an empty path after recalculation.")
                return

        # Get the next target coordinates
        target_coordinates = self.path[0]
        cell_contents = self.model.grid.get_cell_list_contents([target_coordinates])
        other_cars = [obj for obj in cell_contents if isinstance(obj, CarAgent) and obj != self]

        # Get the allowed directions for the current position
        allowed_directions = optionMap.get(self.pos, {})

        # Calculate movement direction
        direction = None
        if target_coordinates[0] > self.pos[0]:
            direction = "down"
        elif target_coordinates[0] < self.pos[0]:
            direction = "up"
        elif target_coordinates[1] > self.pos[1]:
            direction = "right"
        elif target_coordinates[1] < self.pos[1]:
            direction = "left"

        # Check if the movement direction is allowed
        if direction not in allowed_directions:
            print(f"Car {self.unique_id} cannot move {direction} from {self.pos}.")
            self.jammedCounter += 1
            return

        # Check if a semaphore is at the target position
        semaphore = next(
            (agent for agent in self.model.schedule.agents if isinstance(agent, TrafficLightAgent) and agent.pos == target_coordinates),
            None
        )
        can_move = semaphore is None or semaphore.state == "green"

        # Check for other cars in the target cell
        if other_cars:
            for other_car in other_cars:
                my_action, my_reward = self.negotiate(other_car)
                print(f"Car {self.unique_id} negotiating with Car {other_car.unique_id}: My action: {my_action}, Reward: {my_reward}")
                if my_action == "Yield":
                    self.jammedCounter += 1
                    return  # Wait if the action is to yield

        # Move the car if allowed
        if can_move and not other_cars:
            print(f"Car {self.unique_id} at {self.pos} moving towards {target_coordinates}")
            self.model.grid.move_agent(self, target_coordinates)
            self.pos = target_coordinates
            self.path.pop(0)  # Remove the first element in the path since we're moving to it
            self.jammedCounter = 0  # Reset jammed counter
            self.state = "happy"  # Set state to happy whenever the car moves
            self.happiness = min(self.happiness + 10, 100)  # Increase happiness, max at 100
        else:
            print(f"Car {self.unique_id} at {self.pos} waiting; can_move: {can_move}, jammedCounter: {self.jammedCounter}")
            self.jammedCounter += 1
                    
    def step(self):
        self.move()
