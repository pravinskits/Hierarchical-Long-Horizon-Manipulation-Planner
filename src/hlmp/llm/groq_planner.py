import os
import time
import json
import logging
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None

from .schemas import (
    LLMPlanSchema, MissingAPIKey, LLMConnectionError,
    LLMTimeoutError, InvalidLLMResponse, SchemaValidationError, UnsupportedLLMPlan
)
from .base_planner import BaseLLMPlanner
from src.hlmp.core.plan_models import Plan, PlannedSubgoal
from src.hlmp.core.planner import SKILL_REGISTRY

class GroqPlanner(BaseLLMPlanner):
    def __init__(self, config: Dict[str, Any], logger: logging.Logger = None):
        load_dotenv()
        self.config = config.get("llm", {})
        self.logger = logger or logging.getLogger(__name__)
        
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = self.config.get("model", "llama3-8b-8192")
        self.temperature = self.config.get("temperature", 0.0)
        self.timeout = self.config.get("timeout", 10.0)
        
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key, max_retries=2, timeout=self.timeout)
            except ImportError:
                self.logger.error("groq library not installed")
                
    def _build_system_prompt(self, scene_state: Dict[str, Any]) -> str:
        skills = list(SKILL_REGISTRY.values())
        return f"""You are a high-level robot task planner.
Rules:
1. Decompose the user's goal into executable subgoals.
2. Use ONLY skills provided in the allowed skill list: {skills}.
3. Never invent a skill.
4. Never directly control robot joints.
5. Never output Python code.
6. Never output PyBullet commands.
7. Return only the required structured JSON plan matching the schema.
8. Maintain logical dependencies.
9. Prefer simple executable plans.
10. Do not skip required manipulation stages.
11. Respect object and target information supplied by the environment.
12. Do not invent objects that are not present.
13. If the task is unsupported, return a structured planning error.

Scene State:
{json.dumps(scene_state, indent=2)}

Output strictly valid JSON matching the schema."""

    def generate_plan(self, goal: str, scene_state: Dict[str, Any]) -> Plan:
        start_time = time.time()
        self.logger.info("LLM_PLAN_START")
        
        if not self.api_key or not self.client:
            self.logger.error("Missing GROQ_API_KEY")
            raise MissingAPIKey("GROQ_API_KEY not configured.")
            
        sys_prompt = self._build_system_prompt(scene_state)
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"Goal: {goal}"}
                ],
                model=self.model,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            
        except Exception as e:
            msg = str(e).lower()
            if "timeout" in msg:
                raise LLMTimeoutError(str(e))
            raise LLMConnectionError(str(e))
            
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            raise InvalidLLMResponse("LLM returned invalid JSON.")
            
        try:
            validated = LLMPlanSchema.from_dict(parsed)
        except Exception as e:
            raise SchemaValidationError(f"Schema validation failed: {str(e)}")
            
        subgoals = []
        for sg in validated.subgoals:
            psg = PlannedSubgoal(
                id=sg.id,
                skill=sg.skill,
                parameters=sg.parameters,
                preconditions=sg.preconditions,
                expected_outcome=sg.expected_outcome,
                dependencies=sg.dependencies,
                priority=sg.priority
            )
            subgoals.append(psg)
            
        import uuid
        plan = Plan(
            plan_id=f"plan_llm_{uuid.uuid4().hex[:8]}",
            original_goal=goal,
            subgoals=subgoals,
            created_at=time.time(),
            planner_type="groq"
        )
        
        latency = time.time() - start_time
        self.logger.info(f"LLM_PLAN_SUCCESS | Latency: {latency:.2f}s")
        return plan
