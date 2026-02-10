#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.portfolio_stack import PortfolioStack

app = cdk.App()

PortfolioStack(
    app,
    "CodeByCarsonStack",
    env=cdk.Environment(account="420665616125", region="us-east-1"),
)

app.synth()
