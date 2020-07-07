from aws_cdk import aws_apigateway as _apigw
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as _logs
from aws_cdk import core

import os
import json


class global_args:
    """"
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "serverless-async-lambda-api"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_07_05"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class ApiGwLambdaStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        back_end_api_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Create Serverless Event Processor using Lambda):
        # Read Lambda Code):
        try:
            with open("serverless_async_lambda_api/stacks/back_end/lambda_src/get_square.py", mode="r") as f:
                get_square_fn_code = f.read()
        except OSError as e:
            print("Unable to read Lambda Function Code")
            raise e

        get_square_fn = _lambda.Function(
            self,
            "getSquareFn",
            function_name="get_square_fn",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="index.lambda_handler",
            code=_lambda.InlineCode(get_square_fn_code),
            timeout=core.Duration.seconds(15),
            reserved_concurrent_executions=1,
            environment={
                "LOG_LEVEL": "DEBUG",
                "Environment": "Production",
                "ANDON_CORD_PULLED": "False"
            }
        )
        get_square_fn_version = get_square_fn.latest_version
        get_square_fn_version_alias = _lambda.Alias(
            self,
            "greeterFnAlias",
            alias_name="MystiqueAutomation",
            version=get_square_fn_version
        )
        ######

        # Create Custom Loggroup
        # /aws/lambda/function-name
        get_square_fn_fn_lg = _logs.LogGroup(
            self,
            "squareFnLoggroup",
            log_group_name=f"/aws/lambda/{get_square_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Add API GW front end for the Lambda
        back_end_01_api_stage_options = _apigw.StageOptions(
            stage_name="miztiik",
            throttling_rate_limit=10,
            throttling_burst_limit=100,
            logging_level=_apigw.MethodLoggingLevel.INFO
        )

        # Create API Gateway
        api_01 = _apigw.RestApi(
            self,
            "backEnd01Api",
            rest_api_name=f"{back_end_api_name}",
            deploy_options=back_end_01_api_stage_options,
            endpoint_types=[
                _apigw.EndpointType.REGIONAL
            ]
        )

        # InvocationType='RequestResponse' if async_ else 'Event'

        back_end_01_api_res = api_01.root.add_resource("square")
        get_square = back_end_01_api_res.add_resource("{number}")

        # API VTL Template mapping
        # https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integration-async.html
        # https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
        # https://aws.amazon.com/premiumsupport/knowledge-center/custom-headers-api-gateway-lambda/
        req_template = f'{{"number": "$input.params("number")"}}'
        """
        resp_template ='''
            {
                "message": "Received Event! $util.escapeJavaScript($input.json('$.square'))",
                "stage": "$context.stage",
                "request_id": "$context.requestId",
                "resource_path": "$context.resourcePath,
                "http_method": "$context.httpMethod",
                "source_ip": "$context.identity.sourceIp",
                "user-agent": "$context.identity.userAgent",
                "headers": {
                    #foreach($param in $input.params().header.keySet())
                    "$param": "$util.escapeJavaScript($input.params().header.get($param))"
                    #if($param=="InvocationType" && $util.escapeJavaScript($input.params().header.get($param)) == "Event")
                    "is_async":True
                    #end
                    #if($foreach.hasNext),#end
                    #end
                }
            }
            '''
        """
        # We are going to loop through the headers. Find the key:value for asynchrony i.e "InvocationType:Event"
        # If the headers are found, set is_async to true
        # If not found, return the response from lambda
        resp_template = """{
        "api_stage": "$context.stage",
        "api_request_id": "$context.requestId",
        "api_resource_path": "$context.resourcePath",
        "http_method": "$context.httpMethod",
        "source_ip": "$context.identity.sourceIp",
        "user-agent": "$context.identity.userAgent",
        #set($num_square = $util.escapeJavaScript($!input.json('$.square')))
        #foreach($param in $input.params().header.keySet())
        #if($param == "invocationtype" or $param == "InvocationType" && $util.escapeJavaScript($input.params().header.get($param)) == "Event")
        #set($is_async = "true")
        #end
        #end
        #if($is_async == "true")
        "asynchronous_invocation":"true",
        "message":"Event received. Check queue/logs for status"
        #else
        "synchronous_invocation":"true",
        "square_of_your_number_is":$!{num_square}
        #end
        }
        """

        get_square_method_get = get_square.add_method(
            http_method="GET",
            request_parameters={
                "method.request.header.InvocationType": True,
                "method.request.path.number": True
            },
            integration=_apigw.LambdaIntegration(
                handler=get_square_fn,
                proxy=False,
                request_parameters={
                    "integration.request.path.number": "method.request.path.number",
                    "integration.request.header.X-Amz-Invocation-Type": "method.request.path.InvocationType",
                    "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
                },
                passthrough_behavior=_apigw.PassthroughBehavior.WHEN_NO_TEMPLATES,
                request_templates={"application/json": f"{req_template}"},
                integration_responses=[
                    _apigw.IntegrationResponse(
                        status_code="200",
                        # selection_pattern="2\d{2}",  # Use for mapping Lambda Errors
                        response_parameters={

                        },
                        response_templates={
                            "application/json": f"{resp_template}"}
                    )
                ]
            ),
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Length": True,
                    },
                    response_models={
                        "application/json": _apigw.EmptyModel()
                    }
                )
            ]
        )

        # Outputs
        output_1 = core.CfnOutput(
            self,
            "GetSquareApiUrl",
            value=f"{get_square.url}",
            description="Use a browser to access this url"
        )
