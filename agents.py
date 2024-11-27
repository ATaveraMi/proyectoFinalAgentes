from mesa import Agent
import random
from mesa.space import MultiGrid
from dijkstra import dijkstra
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
        self.state = "yellow"

        # Timers iniciales según el estado
        if state == "green":
            self.timer = 5  # Duración del verde
        elif state == "yellow":
            self.timer = 2  # Duración del amarillo
        else:  # Estado rojo
            self.timer = 7  # Duración del rojo

    """
    Cambia el estado del semáforo cada cierto tiempo,
    incluyendo el estado amarillo entre verde y rojo.
    """
    def step(self):
        self.timer -= 1
        if self.timer == 0:
            if self.state == "green":
                self.state = "yellow"
                self.timer = 2  # Duración del amarillo
            elif self.state == "yellow":
                self.state = "red"
                self.timer = 7  # Duración del rojo
            elif self.state == "red":
                self.state = "green"
                self.timer = 5  # Duración del verde

class ParkingSpotAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_occupied = False  # Initially, no car is in the spot

    def step(self):
        # Implement behavior for cars parking/unparking if needed
        pass

class CarAgent(Agent):
    def __init__(self, unique_id, model, agent_type="neutral"):
        super().__init__(unique_id, model)
        self.state = "happy"
        self.happiness = 100
        self.jammedCounter = 0
        self.path = []
        self.last_negotiation = None
        self.agent_type = agent_type if agent_type else random.choice(["cooperative", "competitive", "neutral"])
        self.reward_matrix = {
            ("Yield", "Yield"): (3, 3),
            ("Yield", "Advance"): (2, 4),
            ("Advance", "Yield"): (4, 2),
            ("Advance", "Advance"): (1, 1)
        }
        self.wait_time = 0  # Tracks how long the car has been waiting.

    def negotiate(self, other_agent):
        # Negotiate actions based on agent types
        if self.agent_type == "competitive" and other_agent.agent_type == "competitive":
            my_action, other_action = "Advance", "Advance"
        elif self.agent_type == "cooperative":
            my_action, other_action = "Yield", "Advance"
        elif other_agent.agent_type == "cooperative":
            my_action, other_action = "Advance", "Yield"
        else:
            my_action, other_action = "Yield", "Yield"

        # Get rewards based on actions
        my_reward, other_reward = self.reward_matrix[(my_action, other_action)]

        # Update negotiation result
        self.last_negotiation = my_action
        return my_action, my_reward

    def move(self):
        # Determine valid moves based on traffic lights and other cars
        allowed_directions = optionMap.get(self.pos, {})
        possible_moves = []

        for direction, weight in allowed_directions.items():
            next_pos = {
                "up": (self.pos[0], self.pos[1] + 1),
                "down": (self.pos[0], self.pos[1] - 1),
                "left": (self.pos[0] - 1, self.pos[1]),
                "right": (self.pos[0] + 1, self.pos[1])
            }.get(direction, None)

            if next_pos and not self.model.grid.out_of_bounds(next_pos):
                cell_contents = self.model.grid.get_cell_list_contents([next_pos])
                if not any(isinstance(agent, CarAgent) for agent in cell_contents):
                    possible_moves.append((next_pos, direction))

        # Filter moves based on semaphores
        valid_moves = []
        for next_pos, direction in possible_moves:
            semaphore = next(
                (agent for agent in self.model.schedule.agents if isinstance(agent, TrafficLightAgent) and agent.pos == next_pos),
                None
            )
            if semaphore:
                # Decidir si ignorar el semáforo según el estado de ánimo
                if semaphore.state == "red":
                    ignore_chance = 0
                    if self.state == "angry":
                        ignore_chance = 0.5  # 50% de ignorar
                    elif self.state == "furious":
                        ignore_chance = 0.8  # 80% de ignorar
                    if random.random() < ignore_chance:
                        valid_moves.append((next_pos, direction))  # Ignorar semáforo
                elif semaphore.state == "green":
                    valid_moves.append((next_pos, direction))  # Seguir si está verde
            else:
                valid_moves.append((next_pos, direction))  # Sin semáforo, se permite moverse

        # Elegir un movimiento o esperar
        if valid_moves:
            chosen_move, direction = random.choice(valid_moves)
            self.model.grid.move_agent(self, chosen_move)
            self.pos = chosen_move
            self.jammedCounter = 0
            self.wait_time = 0  # Reiniciar tiempo de espera después de moverse
            self.path.append(self.pos)
            self.happiness += 1
        else:
            self.jammedCounter += 1
            self.wait_time += 1  # Incrementar tiempo de espera
            if self.wait_time > 5:
                self.state = "angry"
                self.happiness -= 20

    def step(self):
        # Check for nearby agents and negotiate if needed
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
        for agent in neighbors:
            if isinstance(agent, CarAgent) and agent != self:
                self.negotiate(agent)

        # Attempt to move
        self.move()
        print(f"Car path: {self.path}")
        # Update state based on happiness
        if self.happiness <= 60:
            self.state = "angry"
        elif self.happiness <= 30:
            self.state = "furious"
        else:
            self.state = "happy"

class ParkingCarAgent(Agent):
    def __init__(self, unique_id, model, starting_pos, target_pos, path, agent_type="neutral"):
        super().__init__(unique_id, model)
        self.starting_pos = starting_pos
        self.target_pos = target_pos
        self.path = path
        self.state = "happy"
        self.happiness = 100
        self.reached_goal = False
        self.jammedCounter = 0
        self.path2 = []
        self.agent_type = agent_type  # "cooperative", "competitive", "neutral"
        self.last_negotiation = None
        self.free_to_go = False
        self.reward_matrix = {
            ("Yield", "Yield"): (5, 5),
            ("Yield", "Advance"): (2, 8),
            ("Advance", "Yield"): (8, 2),
            ("Advance", "Advance"): (3, 3)
        }

    def recalculateNewPath(self):
        # Recalculate a new path if car is jammed
        self.path = dijkstra(self.model.G, self.pos, self.target_pos)
        self.jammedCounter = 0
    
    def move_to_new_location(self):
        return random.randint(0,1) == 0
    


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
            if isinstance(agent, ParkingCarAgent) and agent != self:
                messages.append({
                    "agent_id": agent.unique_id,
                    "position": agent.pos,
                    "intention": "moving" if agent.path else "waiting"
                })
        return messages

    def move(self):

        
        if self.pos == self.target_pos:
            if not self.reached_goal:
                self.reached_goal = True
                print(f"Car {self.unique_id} has reached its destination.")
            
            # Decide to move to a new target position
            if self.model.endList and random.random() < 0.01:  # 1% chance to move
                old_pos = self.target_pos
                self.target_pos = random.choice(self.model.endList)
                self.model.endList.remove(self.target_pos)
                self.model.endList.append(old_pos)
                self.recalculateNewPath()
                self.reached_goal = False  # Reset reached goal
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

        """
        ESTA PARTE por alguna razon tenia las direcciones chuecas
        - Orla
        """
        # Calculate movement direction
        direction = None
        targetX, targetY = target_coordinates
        carX, carY = self.pos

        print(self.pos)
        print(self.path)
        
        if targetX > carX:
            direction = "right"
        elif targetX < carX:
            direction = "left"
        elif targetY > carY:
            direction = "up"
        elif targetY < carY:
            direction = "down"

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
            self.path2.append(self.pos)
        else:
            print(f"Car {self.unique_id} at {self.pos} waiting; can_move: {can_move}, jammedCounter: {self.jammedCounter}")
            self.jammedCounter += 1
                    

    def step(self):
        self.move()
        print(f"ParkingCar path: {self.path2}")

class AmbulanceAgent(Agent):
    def __init__(self, unique_id, model, agent_type="wreckless"):
        super().__init__(unique_id, model)
        self.state = "wreckless"
        self.jammedCounter = 0
        self.agent_type = agent_type
        self.last_passed_lights = set()
        self.current_direction = random.choice(["up", "down", "left", "right"])
        self.pos = None 
        self.path = []

    def move(self):
        allowed_directions = optionMap.get(self.pos, {})
        possible_moves = []

        for direction, weight in allowed_directions.items():
            next_pos = {
                "up": (self.pos[0], self.pos[1] + 1),
                "down": (self.pos[0], self.pos[1] - 1),
                "left": (self.pos[0] - 1, self.pos[1]),
                "right": (self.pos[0] + 1, self.pos[1])
            }.get(direction, None)

            if next_pos and not self.model.grid.out_of_bounds(next_pos):
                cell_contents = self.model.grid.get_cell_list_contents([next_pos])
                if not any(isinstance(agent, CarAgent) for agent in cell_contents):
                    possible_moves.append((next_pos, direction))

        valid_moves = []
        for next_pos, direction in possible_moves:
            semaphore = next(
                (agent for agent in self.model.schedule.agents if isinstance(agent, TrafficLightAgent) and agent.pos == next_pos),
                None
            )

            if semaphore:
                if semaphore.state == "red":
                    ignore_chance = 0.9
                elif semaphore.state == "green":
                    valid_moves.append((next_pos, direction))
            else:
                valid_moves.append((next_pos, direction))

        if valid_moves:
            chosen_move = random.choice(valid_moves) 
            self.model.grid.move_agent(self, chosen_move[0])
            self.pos = chosen_move[0]
            self.current_direction = chosen_move[1]
            self.jammedCounter = 0
            self.path.append(self.pos)

    def step(self):
        # Intentar moverse
        self.move()
        print(f"Ambulance path: {self.path}")


