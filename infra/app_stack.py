# infra/app_stack.py
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_lambda_event_sources as lambda_events,
    aws_glue as glue,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
)
import os
from constructs import Construct


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stage = stage
        
        # Get CORS origin from environment variable or use default based on stage
        cors_origin = os.environ.get(
            "CORS_ORIGIN",
            "http://localhost:5173" if stage == "dev" else "*"
        )
        
        # For API Gateway, use ALL_ORIGINS when wildcard is specified
        api_cors_origins = apigw.Cors.ALL_ORIGINS if cors_origin == "*" else [cors_origin]

        # ---------- DynamoDB: jobs table ----------
        jobs_table = dynamodb.Table(
            self,
            "JobsTable",
            table_name=f"evnmck-baseball-{stage}-jobs",
            partition_key=dynamodb.Attribute(
                name="jobId",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN,
        )

        # ---------- S3: upload bucket ----------
        upload_bucket = s3.Bucket(
            self,
            "UploadBucket",
            bucket_name=f"evnmck-baseball-uploads-{stage}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN,
            auto_delete_objects=True if stage == "dev" else False,
        )

        upload_bucket.add_cors_rule(
            allowed_methods=[
                s3.HttpMethods.PUT,
                s3.HttpMethods.GET,
                s3.HttpMethods.HEAD,
            ],
            allowed_origins=[cors_origin],
            allowed_headers=["*"],  # or ["Content-Type"] if you want to be strict
            exposed_headers=["ETag"],
            max_age=3000,
        )

        # ---------- Shared Lambda Layer ----------
        shared_layer = _lambda.LayerVersion(
            self, "SharedLayer",
            code=_lambda.Code.from_asset("../backend/layers/shared"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        # ---------- Lambda: API ----------
        api_lambda = _lambda.Function(
            self,
            "ApiLambda",
            function_name=f"evnmck-baseball-{stage}-api",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=_lambda.Code.from_asset("../backend/api"),
            layers=[shared_layer],
            environment={
                "STAGE": stage,
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "UPLOAD_BUCKET_NAME": upload_bucket.bucket_name,
                "API_TOKEN": os.environ.get("API_TOKEN", ""),
                "CORS_ORIGIN": cors_origin,
            },
        )

        # Permissions
        jobs_table.grant_read_write_data(api_lambda)
        upload_bucket.grant_read_write(api_lambda)

        # ---------- API Gateway ----------
        api = apigw.RestApi(
            self,
            "HttpApi",
            rest_api_name=f"evnmck-baseball-{stage}-api",
            deploy_options=apigw.StageOptions(
                stage_name=stage,
                throttling_rate_limit=100,
                throttling_burst_limit=50,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
            # can restrict later
            allow_origins=api_cors_origins,
            allow_methods=["GET", "POST", "PUT", "OPTIONS"],
            allow_headers=["Content-Type", "X-API-TOKEN"],
            ),
        )

        # Root /uploads -> POST
        uploads_res = api.root.add_resource("uploads")
        uploads_res.add_method(
            "POST",
            apigw.LambdaIntegration(api_lambda),
        )

        # /jobs/{jobId} -> GET
        jobs_res = api.root.add_resource("jobs")
        job_id_res = jobs_res.add_resource("{jobId}")
        job_id_res.add_method(
            "GET",
            apigw.LambdaIntegration(api_lambda),
        )

        # /jobs/{jobId}/status -> PUT
        status_res = job_id_res.add_resource("status")
        status_res.add_method(
            "PUT",
            apigw.LambdaIntegration(api_lambda),
        )

        # (Optional) /health -> GET
        health_res = api.root.add_resource("health")
        health_res.add_method(
            "GET",
            apigw.LambdaIntegration(api_lambda),
        )

        # ---------- DynamoDB: WebSocket connections table ----------
        websocket_connections_table = dynamodb.Table(
            self,
            "WebSocketConnectionsTable",
            table_name=f"evnmck-baseball-{stage}-websocket-connections",
            partition_key=dynamodb.Attribute(
                name="connectionId",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )

        # ---------- WebSocket API Gateway ----------
        websocket_api = apigwv2.WebSocketApi(
            self,
            "JobStatusWebSocket",
            route_selection_expression="$request.body.action"
        )

        websocket_stage = apigwv2.WebSocketStage(
            self,
            "WebSocketStage",
            web_socket_api=websocket_api,
            stage_name=stage,
            throttle=apigwv2.ThrottleSettings(
                rate_limit=10000,
                burst_limit=5000
            )
        )

        # ---------- WebSocket Lambdas ----------
        # $connect Lambda
        websocket_connect = _lambda.Function(
            self,
            "WebSocketConnect",
            function_name=f"evnmck-baseball-{stage}-websocket-connect",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="connect.handler",
            code=_lambda.Code.from_asset("../backend/websocket"),
            environment={
                "WEBSOCKET_CONNECTIONS_TABLE": websocket_connections_table.table_name,
            }
        )
        websocket_connections_table.grant_write_data(websocket_connect)

        # $disconnect Lambda
        websocket_disconnect = _lambda.Function(
            self,
            "WebSocketDisconnect",
            function_name=f"evnmck-baseball-{stage}-websocket-disconnect",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="disconnect.handler",
            code=_lambda.Code.from_asset("../backend/websocket"),
            environment={
                "WEBSOCKET_CONNECTIONS_TABLE": websocket_connections_table.table_name,
            }
        )
        websocket_connections_table.grant_write_data(websocket_disconnect)

        # send_job_update Lambda
        websocket_send_update = _lambda.Function(
            self,
            "WebSocketSendUpdate",
            function_name=f"evnmck-baseball-{stage}-websocket-send-update",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="send_update.handler",
            code=_lambda.Code.from_asset("../backend/websocket"),
            environment={
                "WEBSOCKET_CONNECTIONS_TABLE": websocket_connections_table.table_name,
                "WEBSOCKET_ENDPOINT": f"https://{websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{stage}",
            },
            timeout=Duration.seconds(30)
        )
        websocket_connections_table.grant_read_data(websocket_send_update)
        
        # Grant permission to invoke post_to_connection
        websocket_send_update.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:Invoke"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/*/@connections/*"
                ]
            )
        )

        # Connect WebSocket Lambdas to routes using lower-level constructs
        # $connect integration
        connect_integration = apigwv2.CfnIntegration(
            self,
            "ConnectIntegration",
            api_id=websocket_api.api_id,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigatewayv2:{self.region}:lambda:path/2015-03-31/functions/{websocket_connect.function_arn.split(':')[-1]}/invocations",
        )
        
        apigwv2.CfnRoute(
            self,
            "ConnectRoute",
            api_id=websocket_api.api_id,
            route_key="$connect",
            target=f"integrations/{connect_integration.ref}",
        )
        
        # $disconnect integration
        disconnect_integration = apigwv2.CfnIntegration(
            self,
            "DisconnectIntegration",
            api_id=websocket_api.api_id,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigatewayv2:{self.region}:lambda:path/2015-03-31/functions/{websocket_disconnect.function_arn.split(':')[-1]}/invocations",
        )
        
        apigwv2.CfnRoute(
            self,
            "DisconnectRoute",
            api_id=websocket_api.api_id,
            route_key="$disconnect",
            target=f"integrations/{disconnect_integration.ref}",
        )
        
        # Grant API Gateway permission to invoke the Lambdas
        websocket_connect.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/*",
        )
        
        websocket_disconnect.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/*",
        )

        # Export WebSocket URL for frontend
        CfnOutput(
            self,
            "WebSocketURL",
            value=websocket_api.api_endpoint,
            export_name=f"evnmck-baseball-{stage}-websocket-url",
            description="WebSocket API endpoint URL"
        )

        #---------- Lambda A: S3 trigger -> Start Step Function ----------
        upload_trigger = _lambda.Function(
            self,
            "UploadTrigger",
            function_name=f"evnmck-baseball-{stage}-upload-trigger",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="upload_trigger.handler",
            code=_lambda.Code.from_asset("../backend/pipeline"),
            layers=[shared_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
            },
        )

        jobs_table.grant_read_write_data(upload_trigger)

        upload_trigger.add_event_source(
            lambda_events.S3EventSource(
                upload_bucket,
                events=[s3.EventType.OBJECT_CREATED_PUT],
                filters=[s3.NotificationKeyFilter(prefix="uploads/")],
            )
        )

        upload_trigger.add_environment("WEBSOCKET_SEND_UPDATE_ARN", websocket_send_update.function_arn)

        upload_trigger.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['lambda:InvokeFunction'],
                resources=[websocket_send_update.function_arn]
            )
        )

        #---------- Lambda B: Error handler for Step Function ----------
        error_handler = _lambda.Function(
            self,
            "ErrorHandler",
            function_name=f"evnmck-baseball-{stage}-error-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="error_handler.handler",
            code=_lambda.Code.from_asset("../backend/pipeline"),
            layers=[shared_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
            },
        )

        jobs_table.grant_read_write_data(error_handler)

        error_handler.add_environment("WEBSOCKET_SEND_UPDATE_ARN", websocket_send_update.function_arn)

        error_handler.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['lambda:InvokeFunction'],
                resources=[websocket_send_update.function_arn]
            )
        )

        # ---------- IAM role for Glue job ----------
        glue_role = iam.Role(
            self, "GlueJobRole",
            role_name=f"evnmck-baseball-{stage}-glue-role",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
        )

        glue_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
        )

        # Grant S3 access
        upload_bucket.grant_read_write(glue_role)
        
        # Grant DynamoDB access to Glue role for updating job status
        jobs_table.grant_read_write_data(glue_role)

        glue_script_asset = s3_assets.Asset(
            self, "GlueScript",
            path="../data/glue/process.py"
        )
        
        # Grant Glue role read access to the script asset
        glue_script_asset.grant_read(glue_role)

        # ---------- Glue job ----------
        glue_default_args = {
            "--TempDir": f"s3://{upload_bucket.bucket_name}/temp/",
            "--job-bookmark-option": "job-bookmark-enable",
            "--additional-python-modules": "pandas==2.2.0",
            "--JOBS_TABLE_NAME": jobs_table.table_name,
        }
        
        # Dev only: add test defaults for manual testing
        if stage == "dev":
            glue_default_args.update({
                "--jobId": "test_id",
                "--bucket": upload_bucket.bucket_name,
                "--key": "tests_data/test_id/yankees_games_test.csv",
            })
        
        glue_job = glue.CfnJob(
            self, "DataProcessingJob",
            name=f"evnmck-baseball-{stage}-processing",
            role=glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=glue_script_asset.s3_object_url,
            ),
            default_arguments=glue_default_args,
        )

        # ---------- Step Function: Glue job orchestration ----------
        # Start Glue job
        start_glue_job = sfn_tasks.GlueStartJobRun(
            self,
            "StartGlueJob",
            glue_job_name=glue_job.name,
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            arguments=sfn.TaskInput.from_object({
                "--jobId.$": "$.jobId",
                "--bucket.$": "$.bucket",
                "--key.$": "$.key",
            }),           
        )

        # Handle failure - invoke error handler Lambda
        handle_failure = sfn_tasks.LambdaInvoke(
            self,
            "HandleJobFailure",
            lambda_function=error_handler,
            payload=sfn.TaskInput.from_object({
                "jobId.$": "$.jobId",
                "error.$": "$.error.Error",
                "cause.$": "$.error.Cause",
            }),
        )

        # Fail state for job failures (ensures execution reflects failure)
        job_failed = sfn.Fail(
            self,
            "JobFailed",
            error="GlueJobFailed",
            cause="The Glue job execution failed and was handled"
        )

        send_update_task = sfn_tasks.LambdaInvoke(
            self,
            "SendJobUpdate",  # Task name
            lambda_function=websocket_send_update,  # Which Lambda to call
            payload=sfn.TaskInput.from_object({
                "jobId.$": "$.jobId",  # Pass jobId from input
                "status": "PROCESSED",  # Hard-coded status
            }),
        )


        # Success state
        job_succeeded = sfn.Pass(self, "JobSucceeded")

        # Define workflow with error handling
        # On Glue failure → error handler → fail state
        start_glue_job.add_catch(
            handler=handle_failure,
            errors=["States.ALL"],
            result_path="$.error"
        )
        
        # Error handler transitions to failure state
        handle_failure.next(job_failed)
        
        # Success path
        definition = start_glue_job.next(send_update_task).next(job_succeeded)

        # Create state machine
        state_machine = sfn.StateMachine(
            self,
            "GlueJobOrchestration",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(15),
            state_machine_name=f"evnmck-baseball-{stage}-glue-orchestration",
        )

        # Grant upload trigger permission to trigger state machine
        state_machine.grant_start_execution(upload_trigger)
        
        # Pass state machine ARN to trigger
        upload_trigger.add_environment("STATE_MACHINE_ARN", state_machine.state_machine_arn)

