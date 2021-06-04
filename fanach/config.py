# Configurations of the app

import os


SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY")

mode = "dev"

if mode == "dev":
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
elif mode == "prod":
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

MAX_CONTENT_LENGTH = 2 * 1024 * 1024

SOLUTION_UNREAD = "unread"
SOLUTION_SOLVED = "solved"
