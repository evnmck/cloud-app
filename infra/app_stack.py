# infra/app_stack.py
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_lambda_event_sources as lambda_events,
)
import os
from constructs import Construct


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stage = stage

        # ---------- DynamoDB: jobs table ----------
        jobs_table = dynamodb.Table(
            self,
            "JobsTable",
            table_name=f"jobs-{stage}",
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
            allowed_origins=[
                "http://localhost:5173",  # your dev frontend
                # later you can add your prod origin here, e.g. "https://app.my-domain.com"
            ],
            allowed_headers=["*"],  # or ["Content-Type"] if you want to be strict
            exposed_headers=["ETag"],
            max_age=3000,
        )

        # ---------- Lambda: API ----------
        api_lambda = _lambda.Function(
            self,
            "ApiLambda",
            function_name=f"myapp-{stage}-api",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=_lambda.Code.from_asset("../backend/api"),
            environment={
                "STAGE": stage,
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "UPLOAD_BUCKET_NAME": upload_bucket.bucket_name,
                "API_TOKEN": os.environ.get("API_TOKEN", ""),
            },
        )

        # Permissions
        jobs_table.grant_read_write_data(api_lambda)
        upload_bucket.grant_read_write(api_lambda)

        # ---------- API Gateway ----------
        api = apigw.RestApi(
            self,
            "HttpApi",
            rest_api_name=f"myapp-{stage}-api",
            deploy_options=apigw.StageOptions(
                stage_name=stage,
                throttling_rate_limit=100,
                throttling_burst_limit=50,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
            # For dev, this is fine. You can restrict later if you want.
            allow_origins=["http://localhost:5173"],
            # Or: allow_origins=apigw.Cors.ALL_ORIGINS,
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

        # (Optional) /health -> GET
        health_res = api.root.add_resource("health")
        health_res.add_method(
            "GET",
            apigw.LambdaIntegration(api_lambda),
        )

        #---------- Update Lambda -------------
        upload_handler = _lambda.Function(
            self,
            "UploadEventHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="upload_handler.handler",
            code=_lambda.Code.from_asset("../backend/pipeline"),  # for example
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
            },
        )

        jobs_table.grant_read_write_data(upload_handler)

        upload_handler.add_event_source(
            lambda_events.S3EventSource(
                upload_bucket,
                events=[s3.EventType.OBJECT_CREATED_PUT],
                filters=[s3.NotificationKeyFilter(prefix="uploads/")],
            )
        )
