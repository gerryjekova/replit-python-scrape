import json
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfigService:

    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self, name: str) -> Dict[str, Any]:
        try:
            config_path = self.config_dir / f"{name}.json"
            if config_path.exists():
                with open(config_path) as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config {name}: {str(e)}")
        return {}
