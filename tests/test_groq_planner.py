import pytest
import time
from unittest.mock import MagicMock, patch
from src.hlmp.llm.groq_planner import GroqPlanner
from src.hlmp.llm.schemas import MissingAPIKey

@patch("src.hlmp.llm.groq_planner.os.getenv")
def test_missing_api_key(mock_getenv):
    mock_getenv.return_value = None
    planner = GroqPlanner({})
    with pytest.raises(MissingAPIKey):
        planner.generate_plan("Move red to target", {})


