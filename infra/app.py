# infra/app.py
from aws_cdk import App, Environment
from app_stack import AppStack

app = App()

ACCOUNT_ID = app.node.try_get_context("account_id") or "783188002985"
REGION = app.node.try_get_context("region") or "us-east-1"

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
