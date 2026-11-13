"""SMARTFLOW ODISHA backend — configuration.

Conventional-commits style note: feat(config): environment-driven settings.
Secrets come from the environment; defaults are dev-only and must be
overridden in any non-local deployment.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SMARTFLOW ODISHA"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/smartflow.db"
    jwt_secret: str = "dev-only-change-me"  # override via JWT_SECRET env var
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    admin_email: str = "admin@smartflow.local"
    admin_password: str = "ChangeMe123!"  # seed only; change after first login
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Adaptive signal defaults
    green_min_s: int = 10
    green_max_s: int = 60
    yellow_s: int = 3
    all_red_s: int = 2
    demand_k: float = 0.8
    w_queue: float = 0.5
    w_count: float = 0.3
    w_wait: float = 0.2
    # SUMO environment configuration
    sumo_home: str = r"C:\Program Files (x86)\SUMO"
    sumo_binary: str = r"C:\Program Files (x86)\SUMO\bin\sumo.exe"
    sumo_gui_binary: str = r"C:\Program Files (x86)\SUMO\bin\sumo-gui.exe"
    sumo_config: str = "simulation/sumo/config/smartflow.sumocfg"
    simulation_mode: str = "sumo"
    sumo_gui_enabled: bool = False

    model_config = {"env_prefix": "SMARTFLOW_", "extra": "ignore"}


settings = Settings()
