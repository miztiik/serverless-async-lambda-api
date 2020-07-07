#!/usr/bin/env python3

from aws_cdk import core


from serverless_async_lambda_api.stacks.back_end.api_gw_lambda_stack import ApiGwLambdaStack


app = core.App()


# The API GW and Lambda Backend Stack
api_back_end = ApiGwLambdaStack(
    app,
    "serverless-async-lambda-api",
    back_end_api_name="back_end_01_api",
    description="The API GW and Lambda Backend Stack"
)

# Stack Level Tagging
core.Tag.add(app, key="Owner",
             value=app.node.try_get_context("owner"))
core.Tag.add(app, key="OwnerProfile",
             value=app.node.try_get_context("github_profile"))
core.Tag.add(app, key="GithubRepo",
             value=app.node.try_get_context("github_repo_url"))
core.Tag.add(app, key="Udemy",
             value=app.node.try_get_context("udemy_profile"))
core.Tag.add(app, key="SkillShare",
             value=app.node.try_get_context("skill_profile"))
core.Tag.add(app, key="AboutMe",
             value=app.node.try_get_context("about_me"))

app.synth()
