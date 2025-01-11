import os

from dotenv import load_dotenv

load_dotenv()


# Basics
LOCATION = os.getenv("LOCATION", "us-central1")
PROJECT_ID = os.getenv("PROJECT_ID")
IS_TESTING = bool(os.getenv("IS_TESTING"))
LOG_FORMAT = "\n%(levelname)s: %(message)s"

# Defaults
MAX_FILTERS = int(os.getenv("MAX_FILTERS", "3"))
MAX_WEBHOOKS = int(os.getenv("MAX_WEBHOOKS", "2"))

# Firestore Collections
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "users")
