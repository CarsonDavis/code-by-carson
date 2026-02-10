# AWS CDK Best Practices for Static Site Hosting (S3 + CloudFront) -- Early 2026

## Executive Summary

OAI is dead; OAC has fully replaced it. The `S3Origin` class in CDK is deprecated. The current recommended pattern uses `S3BucketOrigin.withOriginAccessControl()`, which was introduced as an L2 construct in late 2024 and automatically provisions the OAC, bucket policy, and KMS key policy. There is no all-in-one L3 construct in `aws-cdk-lib` that bundles CloudFront + S3 + ACM + Route53, but AWS provides an official example construct and the `@aws-solutions-constructs/aws-cloudfront-s3` package handles the CloudFront + S3 portion with strong security defaults. For the full stack, you build your own L3 construct from L2 parts -- it takes about 50 lines of TypeScript.

---

## 1. OAI vs OAC: OAC Has Replaced OAI

**OAI (Origin Access Identity) is legacy.** AWS recommends Origin Access Control (OAC) for all new deployments. In CDK, the `S3Origin` class and `S3BucketOrigin.withOriginAccessIdentity()` are both deprecated.

| Feature | OAI (Legacy) | OAC (Current) |
|---|---|---|
| SSE-KMS support | No | Yes |
| All AWS regions (incl. opt-in) | No | Yes |
| PUT/POST/DELETE to S3 | No | Yes |
| Short-term credentials | No | Yes |
| Credential rotation | No | Automatic |
| Confused deputy protection | Limited | Resource-based policies |
| CDK L2 support | Deprecated | `S3BucketOrigin.withOriginAccessControl()` |

**CDK API mapping:**

| Old (Deprecated) | New (Current) |
|---|---|
| `new S3Origin(bucket)` | `S3BucketOrigin.withOriginAccessControl(bucket)` |
| `new S3Origin(bucket, { originAccessIdentity })` | `S3BucketOrigin.withOriginAccessIdentity(bucket)` (still works, but deprecated) |
| N/A | `S3BucketOrigin.withBucketDefaults(bucket)` (no access control) |
| N/A | `new S3StaticWebsiteOrigin(bucket)` (website endpoint) |

**What `withOriginAccessControl()` does automatically:**
1. Creates an `AWS::CloudFront::OriginAccessControl` resource
2. Updates the S3 bucket policy to grant CloudFront read access
3. Updates the KMS key policy if the bucket uses SSE-KMS
4. Sets `OriginAccessControlId` on the CloudFront distribution origin

**Minimal OAC example:**

```typescript
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';

const bucket = new s3.Bucket(this, 'SiteBucket');
new cloudfront.Distribution(this, 'Dist', {
  defaultBehavior: {
    origin: origins.S3BucketOrigin.withOriginAccessControl(bucket),
  },
});
```

That is it. The OAC, bucket policy, and origin configuration are all handled.

---

## 2. L3 / High-Level Constructs for Static Sites

### What ships with `aws-cdk-lib`: Nothing at L3 level

There is no built-in L3 construct in `aws-cdk-lib` that combines S3 + CloudFront + ACM + Route53. You compose L2 constructs yourself.

### `@aws-solutions-constructs/aws-cloudfront-s3` (AWS-maintained)

This is the closest thing to an official L3 construct for the CloudFront + S3 pattern. It is maintained by the AWS Solutions Constructs team (separate npm package, not part of `aws-cdk-lib`).

**What it provisions:**
- CloudFront distribution with OAC (not OAI)
- S3 content bucket (or accepts existing)
- S3 access logging bucket
- CloudFront access logging bucket
- HTTP security headers injected by default
- Minimal bucket policy (only `s3:GetObject` + `s3:ListBucket`, scoped to the distribution ARN)

**What it does NOT include:** ACM certificate, Route53 records, `BucketDeployment`. You add those yourself.

```typescript
import { CloudFrontToS3 } from '@aws-solutions-constructs/aws-cloudfront-s3';

const cfToS3 = new CloudFrontToS3(this, 'StaticSite', {
  // All optional -- sensible defaults applied
  insertHttpSecurityHeaders: true, // default
});

// Access the created resources:
cfToS3.cloudFrontWebDistribution; // CloudFront Distribution
cfToS3.s3BucketInterface;         // S3 Bucket
```

### `aws-cdk-examples` StaticSite construct (reference implementation)

AWS provides an official example in the `aws-cdk-examples` repository that IS a full CloudFront + S3 + ACM + Route53 construct. It is not a published package -- it is a reference you copy and adapt.

### `aws-s3-deployment` (`BucketDeployment`)

This L2 construct handles uploading local files to S3 and optionally invalidating CloudFront cache paths:

```typescript
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';

new s3deploy.BucketDeployment(this, 'Deploy', {
  sources: [s3deploy.Source.asset('./site-contents')],
  destinationBucket: siteBucket,
  distribution: cfDistribution,
  distributionPaths: ['/*'],
});
```

---

## 3. Recommended Security Posture

### S3 Bucket Configuration

```typescript
const siteBucket = new s3.Bucket(this, 'SiteBucket', {
  // Block all public access -- CloudFront accesses via OAC, not public URL
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  publicReadAccess: false,

  // Enforce HTTPS for all requests to S3
  enforceSSL: true,

  // Encryption at rest (SSE-S3 is default, SSE-KMS for stricter requirements)
  encryption: s3.BucketEncryption.S3_MANAGED,
  // For SSE-KMS:
  // encryption: s3.BucketEncryption.KMS,
  // encryptionKey: myKmsKey,
  // bucketKeyEnabled: true, // reduces KMS API costs

  // Object ownership required for OAC
  objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,

  // Versioning (optional, useful for rollbacks)
  versioned: false, // enable if you need content rollback

  // Cleanup policy for dev/staging
  removalPolicy: RemovalPolicy.DESTROY,
  // NOTE: autoDeleteObjects is incompatible with OAC -- see known issues below
});
```

### CloudFront Distribution Configuration

```typescript
const distribution = new cloudfront.Distribution(this, 'Distribution', {
  defaultBehavior: {
    origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket),
    compress: true,
    allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    // Security headers
    responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
  },
  defaultRootObject: 'index.html',
  minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
  // Custom error responses for SPA routing
  errorResponses: [
    {
      httpStatus: 403,
      responseHttpStatus: 200,
      responsePagePath: '/index.html',
      ttl: Duration.minutes(5),
    },
    {
      httpStatus: 404,
      responseHttpStatus: 200,
      responsePagePath: '/index.html',
      ttl: Duration.minutes(5),
    },
  ],
});
```

### Security Headers

Two approaches:

**Option A: AWS-managed policy (simplest)**
```typescript
responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
```

**Option B: Custom policy (more control)**
```typescript
const securityHeaders = new cloudfront.ResponseHeadersPolicy(this, 'SecurityHeaders', {
  securityHeadersBehavior: {
    strictTransportSecurity: {
      accessControlMaxAge: Duration.seconds(31536000),
      includeSubdomains: true,
      override: true,
    },
    contentTypeOptions: { override: true },
    frameOptions: {
      frameOption: cloudfront.HeadersFrameOption.DENY,
      override: true,
    },
    referrerPolicy: {
      referrerPolicy: cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
      override: true,
    },
  },
});
```

### Bucket Policy (auto-generated by OAC)

When using `S3BucketOrigin.withOriginAccessControl()`, the CDK automatically adds a bucket policy that looks like:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "cloudfront.amazonaws.com"
  },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::bucket-name/*",
  "Condition": {
    "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::account-id:distribution/distribution-id"
    }
  }
}
```

You do not need to write this manually. The CDK handles it.

---

## 4. CDK v2 Changes Since 2024

The most significant change for static site hosting was the **OAC L2 construct release** in late 2024:

| Change | Impact |
|---|---|
| `S3Origin` deprecated | Replace with `S3BucketOrigin.withOriginAccessControl()` |
| `S3BucketOrigin` class introduced | Static factory methods: `.withOriginAccessControl()`, `.withOriginAccessIdentity()`, `.withBucketDefaults()` |
| `S3OriginAccessControl` class introduced | Configurable OAC with signing options |
| `S3StaticWebsiteOrigin` class introduced | For S3 buckets configured as website endpoints |
| `originAccessLevels` parameter | Fine-grained control: READ, READ_VERSIONED, WRITE, DELETE, LIST |
| `aws-solutions-constructs` updated to OAC | `CloudFrontToS3` now uses OAC by default |

No other major changes to core `aws-cdk-lib` constructs for static site hosting beyond incremental updates. The CDK best practices guide has not introduced new patterns beyond what was already established.

---

## 5. Complete Reference Implementation

This is the full pattern for CloudFront + S3 + ACM + Route53, based on the official `aws-cdk-examples` repo and current best practices:

```typescript
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Duration, RemovalPolicy } from 'aws-cdk-lib';
import * as path from 'path';

export interface StaticSiteProps {
  domainName: string;       // e.g., "example.com"
  siteSubDomain: string;    // e.g., "www"
  sitePath: string;         // local path to site contents
}

export class StaticSite extends Construct {
  public readonly distribution: cloudfront.Distribution;
  public readonly siteBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: StaticSiteProps) {
    super(scope, id);

    const siteDomain = `${props.siteSubDomain}.${props.domainName}`;

    // --- DNS Zone ---
    const zone = route53.HostedZone.fromLookup(this, 'Zone', {
      domainName: props.domainName,
    });

    // --- S3 Bucket ---
    this.siteBucket = new s3.Bucket(this, 'SiteBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      publicReadAccess: false,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // --- ACM Certificate (must be in us-east-1 for CloudFront) ---
    const certificate = new acm.Certificate(this, 'Certificate', {
      domainName: siteDomain,
      validation: acm.CertificateValidation.fromDns(zone),
    });

    // --- CloudFront Distribution ---
    this.distribution = new cloudfront.Distribution(this, 'Distribution', {
      certificate: certificate,
      domainNames: [siteDomain],
      defaultRootObject: 'index.html',
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(this.siteBucket),
        compress: true,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
      },
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: Duration.minutes(5),
        },
      ],
    });

    // --- Route53 Alias Record ---
    new route53.ARecord(this, 'AliasRecord', {
      recordName: siteDomain,
      target: route53.RecordTarget.fromAlias(
        new targets.CloudFrontTarget(this.distribution)
      ),
      zone,
    });

    // --- Deploy Site Contents ---
    new s3deploy.BucketDeployment(this, 'DeployContents', {
      sources: [s3deploy.Source.asset(props.sitePath)],
      destinationBucket: this.siteBucket,
      distribution: this.distribution,
      distributionPaths: ['/*'],
    });

    // --- Outputs ---
    new cdk.CfnOutput(this, 'SiteUrl', { value: `https://${siteDomain}` });
    new cdk.CfnOutput(this, 'DistributionId', {
      value: this.distribution.distributionId,
    });
    new cdk.CfnOutput(this, 'BucketName', {
      value: this.siteBucket.bucketName,
    });
  }
}
```

**Usage in a stack:**

```typescript
new StaticSite(this, 'MySite', {
  domainName: 'example.com',
  siteSubDomain: 'www',
  sitePath: path.join(__dirname, '../site-contents'),
});
```

**Important note on ACM certificates:** CloudFront requires the ACM certificate to be in `us-east-1`. If your stack is in another region, you need to either deploy this stack to `us-east-1` or use a cross-region certificate pattern (e.g., a separate stack in `us-east-1` for the certificate, then pass the ARN).

---

## Known Issues and Gotchas

1. **`autoDeleteObjects` is incompatible with OAC.** The custom resource Lambda that auto-deletes objects cannot access the bucket when OAC restricts access to CloudFront only. Use `removalPolicy: RemovalPolicy.DESTROY` without `autoDeleteObjects`, and clean up manually or with a separate Lambda.

2. **Migration from OAI to OAC** should be done in multiple deployments to avoid downtime. First deploy with both OAI and OAC permissions in the bucket policy, then switch the distribution to OAC, then remove OAI permissions.

3. **`S3StaticWebsiteOrigin` vs `S3BucketOrigin.withOriginAccessControl()`**: These serve different purposes. `S3BucketOrigin.withOriginAccessControl()` treats S3 as a REST API endpoint (recommended). `S3StaticWebsiteOrigin` uses S3's static website hosting feature, which requires the bucket to be publicly accessible -- this is generally NOT recommended when using CloudFront with OAC.

4. **S3 Object Ownership** must be set to `BUCKET_OWNER_ENFORCED` (the CDK default) when using OAC.

---

## Decision Matrix: Which Approach to Use

| Scenario | Approach |
|---|---|
| Quick prototype, no custom domain | `S3BucketOrigin.withOriginAccessControl()` + `Distribution` (bare L2s) |
| Production with custom domain | Full L3 pattern: S3 + CloudFront + ACM + Route53 (build your own, ~50 lines) |
| Want security defaults out of the box | `@aws-solutions-constructs/aws-cloudfront-s3` + add ACM/Route53 yourself |
| Migrating from OAI | Multi-step deployment: add OAC policy, switch origin, remove OAI policy |

---

## Sources

- [AWS Blog: New CDK L2 Construct for CloudFront OAC](https://aws.amazon.com/blogs/devops/a-new-aws-cdk-l2-construct-for-amazon-cloudfront-origin-access-control-oac/)
- [AWS CDK v2 CloudFront Origins Module Docs](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront_origins-readme.html)
- [AWS Docs: Restrict Access to S3 Origin](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [AWS CDK Examples: Static Site (TypeScript)](https://github.com/aws-samples/aws-cdk-examples/blob/main/typescript/static-site/static-site.ts)
- [AWS Solutions Constructs: aws-cloudfront-s3](https://docs.aws.amazon.com/solutions/latest/constructs/aws-cloudfront-s3.html)
- [AWS CDK RFC 0617: CloudFront OAC L2](https://github.com/aws/aws-cdk-rfcs/blob/main/text/0617-cloudfront-oac-l2.md)
- [CDK S3BucketOrigin Class Docs](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront_origins.S3BucketOrigin.html)
- [CDK ResponseHeadersPolicy Docs](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.ResponseHeadersPolicy.html)
- [AWS CDK v2 Best Practices Guide](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)
- [GitHub Issue: autoDeleteObjects incompatible with OAC](https://github.com/aws/aws-cdk/issues/31360)
- [GitHub Issue: OAC policy not added when switching buckets](https://github.com/aws/aws-cdk/issues/34279)
