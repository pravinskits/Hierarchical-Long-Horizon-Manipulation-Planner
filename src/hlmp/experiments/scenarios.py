import random

class ScenarioGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(self.seed)
        
    def generate_long_horizon(self, horizon: int) -> str:
        objects = ["red_cube", "blue_cube", "green_cube", "yellow_block", "purple_sphere"]
        targets = ["target_1", "target_2", "bin_A", "bin_B"]
        
        phrases = []
        for _ in range(max(1, horizon // 3)):
            obj = random.choice(objects)
            tgt = random.choice(targets)
            action = random.choice(["move", "push", "place"])
            
            if action == "move":
                phrases.append(f"move {obj} to {tgt}")
            elif action == "push":
                phrases.append(f"push {obj} to {tgt}")
            else:
                phrases.append(f"place {obj} beside {tgt}")
                
        return " and ".join(phrases)
