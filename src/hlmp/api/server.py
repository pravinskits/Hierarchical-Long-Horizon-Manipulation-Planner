import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import yaml

from src.hlmp.database.database import init_db
from src.hlmp.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = config.get("database", {}).get("url", "sqlite:///./data/app.db")
    logger.info(f"Initializing database at {db_url}")
    init_db(db_url)
    
    # Generate initial environment camera frame if not present
    try:
        import src.hlmp.sim.env as sim_env
        if not sim_env.LATEST_FRAME_BYTES:
            from src.hlmp.sim.env import SimulationEnvironment
            from src.hlmp.sim.scene import SceneManager
            from src.hlmp.sim.objects import ObjectManager
            from src.hlmp.sim.robot import RobotArm
            env = SimulationEnvironment(config, logger, headless=True)
            env.connect()
            SceneManager(config, logger, env.client_id).build_scene()
            ObjectManager(config, logger, env.client_id).populate_from_config()
            robot = RobotArm(config, logger, env.client_id)
            robot.load()
            robot.reset_to_initial()
            env._save_camera_frame(force_disk=True)
            env.disconnect()
            logger.info("Initialized simulation camera feed.")
    except Exception as e:
        logger.warning(f"Failed to generate initial simulation frame: {e}")

    logger.info("API started successfully.")
    yield

app = FastAPI(
    title="Hierarchical Long-Horizon Manipulation Planner API",
    description="REST API for the HLMP Robotic Framework",
    version="0.1.0",
    lifespan=lifespan
)

try:
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
except Exception:
    config = {}

cors_origins = config.get("api", {}).get("cors_origins", ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def redirect_to_dashboard():
    return RedirectResponse(url="http://localhost:5173")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred.", "details": str(exc)}}
    )

app.include_router(router)
