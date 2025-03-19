import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    QQWRY_DAT_PATH: Path = DATA_DIR / "qqwry.dat"
    DATABASE_PATH: Path = DATA_DIR / "data.db"
    __prefix: str = "sqlite:///" if sys.platform.startswith("win") else "sqlite:////"
    SQLALCHEMY_DATABASE_URI: str = f"{__prefix}{DATABASE_PATH}"
    DATA_UPDATED_DATE: str | None = os.getenv("DATA_UPDATED_DATE")


class DevelopmentConfig(Config):
    """开发配置"""

    FLASK_ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True


class ProductionConfig(Config):
    """生产配置"""

    FLASK_ENV: Literal["development", "production"] = "production"
    DEBUG: bool = False


load_dotenv()
flask_env = os.getenv("FLASK_ENV", "development")
if flask_env == "development":
    config = DevelopmentConfig
elif flask_env == "production":
    config = ProductionConfig
else:
    raise ValueError(f"未知 FLASK_ENV: {flask_env}")
