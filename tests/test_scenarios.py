from src.hlmp.experiments.scenarios import ScenarioGenerator

def test_deterministic_generation():
    g1 = ScenarioGenerator(seed=42)
    h1 = g1.generate_long_horizon(5)
    
    g2 = ScenarioGenerator(seed=42)
    h2 = g2.generate_long_horizon(5)
    
    assert h1 == h2
