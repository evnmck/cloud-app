from aws_cdk import App, Environment
from app_stack import AppStack
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = App()

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
REGION = os.getenv("REGION")

env = Environment(account=ACCOUNT_ID, region=REGION)

# Dev stack
AppStack(
    app,
    "MyApp-dev",
    stage="dev",
    env=env,
)

# Prod stack
AppStack(
    app,
    "MyApp-prod",
    stage="prod",
    env=env,
)

app.synth()