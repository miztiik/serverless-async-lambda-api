#!/usr/bin/env python3

from aws_cdk import core

from serverless_async_lambda_api.serverless_async_lambda_api_stack import ServerlessAsyncLambdaApiStack


app = core.App()
ServerlessAsyncLambdaApiStack(app, "serverless-async-lambda-api")

app.synth()
