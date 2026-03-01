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
    aws_glue as glue,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
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

        # (Optional) /health -> GET
        health_res = api.root.add_resource("health")
        health_res.add_method(
            "GET",
            apigw.LambdaIntegration(api_lambda),
        )

        #---------- Update Lambda for Pipeline -------------
        upload_handler = _lambda.Function(
            self,
            "UploadEventHandler",
            function_name=f"evnmck-baseball-{stage}-upload-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="upload_handler.handler",
            code=_lambda.Code.from_asset("../backend/pipeline"),
            layers=[shared_layer],
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

        glue_script_asset = s3_assets.Asset(
            self, "GlueScript",
            path="../data/glue/process.py"
        )

        # ---------- Glue job ----------
        glue_job = glue.CfnJob(
            self, "DataProcessingJob",
            name=f"evnmck-baseball-{stage}-processing",
            role=glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=glue_script_asset.s3_object_url,
            ),
            default_arguments={
                "--TempDir": f"s3://{upload_bucket.bucket_name}/temp/",
                "--job-bookmark-option": "job-bookmark-enable",
                "--JOBS_TABLE_NAME": jobs_table.table_name,
            },
        )

        # ---------- Lambda permissions to trigger Glue ----------
        upload_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["glue:StartJobRun"],
                resources=[f"arn:aws:glue:*:*:job/{glue_job.name}"],
            )
        )

        # Pass Glue job name to Lambda
        upload_handler.add_environment("GLUE_JOB_NAME", glue_job.name)

