from pathlib import Path
from dotenv import load_dotenv
import os

# Root directory of the project (one level above src/)
PROJ_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables from .env file
load_dotenv(PROJ_ROOT / ".env")

# Example: access environment variables
API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Data directories
DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Notebooks and source directories
NOTEBOOKS_DIR = PROJ_ROOT / "notebooks"
SRC_DIR = PROJ_ROOT / "src"

# Example usage:
# from src.config import RAW_DATA_DIR
# df = pd.read_csv(RAW_DATA_DIR / "mydata.csv")
