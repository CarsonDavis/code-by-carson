"""CDK stack for the CodeByCarson portfolio site.

Resources: S3 (site + preview), CloudFront + OAC, ACM, Route 53, GitHub OIDC.
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_s3 as s3,
)
from constructs import Construct

DOMAIN = "codebycarson.com"
GITHUB_ORG = "CarsonDavis"
GITHUB_REPO = "code-by-carson"


class PortfolioStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Route 53 hosted zone (must already exist) ──────────────
        zone = route53.HostedZone.from_lookup(self, "Zone", domain_name=DOMAIN)

        # ── ACM certificate (us-east-1 required for CloudFront) ────
        certificate = acm.Certificate(
            self,
            "SiteCert",
            domain_name=DOMAIN,
            subject_alternative_names=[f"www.{DOMAIN}"],
            validation=acm.CertificateValidation.from_dns(zone),
        )

        # ── S3 bucket (site content) ──────────────────────────────
        site_bucket = s3.Bucket(
            self,
            "SiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ── CloudFront distribution with OAC ──────────────────────
        distribution = cloudfront.Distribution(
            self,
            "SiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress=True,
            ),
            domain_names=[DOMAIN, f"www.{DOMAIN}"],
            certificate=certificate,
            default_root_object="index.html",
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
            ],
        )

        # ── DNS records ───────────────────────────────────────────
        route53.ARecord(
            self,
            "ApexAlias",
            zone=zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )
        route53.ARecord(
            self,
            "WwwAlias",
            zone=zone,
            record_name=f"www.{DOMAIN}",
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )

        # ── Preview bucket (for PR previews) ──────────────────────
        preview_bucket = s3.Bucket(
            self,
            "PreviewBucket",
            website_index_document="index.html",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
            removal_policy=RemovalPolicy.DESTROY,
        )

        preview_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[preview_bucket.arn_for_objects("*")],
                principals=[iam.AnyPrincipal()],
            )
        )

        # ── GitHub OIDC provider ──────────────────────────────────
        oidc_provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOidc",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # ── IAM role for GitHub Actions ───────────────────────────
        deploy_role = iam.Role(
            self,
            "GitHubActionsRole",
            assumed_by=iam.FederatedPrincipal(
                oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{GITHUB_ORG}/{GITHUB_REPO}:*",
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="Role assumed by GitHub Actions for CodeByCarson deployments",
        )

        # S3 permissions for both buckets
        site_bucket.grant_read_write(deploy_role)
        preview_bucket.grant_read_write(deploy_role)
        preview_bucket.grant_delete(deploy_role)

        # CloudFront invalidation
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudfront:CreateInvalidation"],
                resources=[
                    f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                ],
            )
        )

        # CDK deploy permissions (CloudFormation + supporting services)
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudformation:*",
                    "s3:*",
                    "cloudfront:*",
                    "route53:*",
                    "acm:*",
                    "iam:*",
                    "ssm:GetParameter",
                    "sts:AssumeRole",
                ],
                resources=["*"],
            )
        )

        # ── Outputs ───────────────────────────────────────────────
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
        CfnOutput(self, "SiteUrl", value=f"https://{DOMAIN}")
        CfnOutput(self, "PreviewBucketName", value=preview_bucket.bucket_name)
        CfnOutput(
            self,
            "PreviewBucketUrl",
            value=preview_bucket.bucket_website_url,
        )
        CfnOutput(self, "GitHubActionsRoleArn", value=deploy_role.role_arn)
