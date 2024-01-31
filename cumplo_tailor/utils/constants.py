import os

from dotenv import load_dotenv

load_dotenv()

CONFIGURATIONS_COLLECTION = os.getenv("CONFIGURATIONS_COLLECTION", "configurations")
IS_TESTING = bool(os.getenv("IS_TESTING"))

LOCATION = os.getenv("LOCATION", "us-central1")
LOG_FORMAT = "\n [%(levelname)s] %(message)s"
MAX_CONFIGURATIONS = int(os.getenv("MAX_CONFIGURATIONS", "3"))
NOTIFICATIONS_COLLECTION = os.getenv("NOTIFICATIONS_COLLECTION", "notifications")
PROJECT_ID = os.getenv("PROJECT_ID")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "users")
