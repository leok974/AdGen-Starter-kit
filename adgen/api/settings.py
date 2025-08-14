# api/settings.py
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field, field_validator
from pathlib import Path
import os

class AppSettings(BaseSettings):
    # MODE: "api" (use Comfy API) or "hotfolder"
    COMFY_MODE: str = Field(default=os.getenv("COMFY_MODE", "api"))
    COMFY_API: AnyHttpUrl | None = os.getenv("COMFY_API") or "http://127.0.0.1:8188"
    RUNS_DIR: Path = Path(os.getenv("RUNS_DIR", "adgen/runs")).resolve()

    @field_validator("COMFY_MODE")
    @classmethod
    def _mode_ok(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in {"api", "hotfolder"}:
            raise ValueError("COMFY_MODE must be 'api' or 'hotfolder'")
        return v

    @field_validator("RUNS_DIR")
    @classmethod
    def _ensure_runs_dir(cls, p: Path) -> Path:
        p.mkdir(parents=True, exist_ok=True)
        return p

settings = AppSettings()

def dump_settings_banner() -> str:
    return (
        "\n=== AdGen Settings ===\n"
        f"COMFY_MODE: {settings.COMFY_MODE}\n"
        f"COMFY_API : {settings.COMFY_API}\n"
        f"RUNS_DIR  : {settings.RUNS_DIR}\n"
        "=======================\n"
    )
