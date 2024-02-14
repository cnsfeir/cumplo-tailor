import os

from dotenv import load_dotenv

load_dotenv()


# Basics
LOCATION = os.getenv("LOCATION", "us-central1")
PROJECT_ID = os.getenv("PROJECT_ID")
IS_TESTING = bool(os.getenv("IS_TESTING"))
LOG_FORMAT = "\n%(levelname)s: %(message)s"

# Defaults
MAX_CONFIGURATIONS = int(os.getenv("MAX_CONFIGURATIONS", "3"))

# Firestore Collections
CONFIGURATIONS_COLLECTION = os.getenv("CONFIGURATIONS_COLLECTION", "configurations")
NOTIFICATIONS_COLLECTION = os.getenv("NOTIFICATIONS_COLLECTION", "notifications")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "users")
