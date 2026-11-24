import os

APP_NAME = os.getenv("APP_NAME", "KONGCHAT Identity Engine")
JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "DEV-ONLY-CHANGE-ME-TO-A-LONG-RANDOM-SECRET"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
DATABASE_URL = os.getenv(
    "KONGCHAT_DATABASE_URL",
    "sqlite:///./kongchat.db"
)
