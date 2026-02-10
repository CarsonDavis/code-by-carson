# Research Background: AWS CDK Best Practices for Static Site Hosting (S3 + CloudFront)

**Date:** 2026-02-09
**Description:** Investigating current AWS CDK v2 best practices for static site hosting using S3 + CloudFront, including OAI vs OAC, L3 constructs, security posture, and combined constructs for CloudFront + S3 + ACM + Route53.

## Sources

[1]: https://aws.amazon.com/blogs/devops/a-new-aws-cdk-l2-construct-for-amazon-cloudfront-origin-access-control-oac/ "AWS Blog: New CDK L2 Construct for CloudFront OAC"
[2]: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront_origins-readme.html "AWS CDK v2 CloudFront Origins Module Docs"
[3]: https://github.com/aws/aws-cdk/issues/21771 "GitHub Issue: CloudFront Support Origin Access Control"
[4]: https://github.com/aws/aws-cdk-rfcs/blob/main/text/0617-cloudfront-oac-l2.md "AWS CDK RFC 0617: CloudFront OAC L2"
[5]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html "AWS Docs: Restrict access to S3 origin"
[6]: https://dev.to/aws-builders/reduce-the-amount-of-code-in-aws-cdk-apply-oac-in-amazon-cloudfront-l2-constructs-27hi "DEV: Reduce code in CDK with OAC L2 constructs"
[7]: https://github.com/aws-samples/aws-cdk-examples/blob/main/typescript/static-site/static-site.ts "AWS CDK Examples: Static Site TypeScript"
[8]: https://github.com/ukautz/aws-cdk-static-website "Community L3: aws-cdk-static-website"
[9]: https://aws.amazon.com/blogs/apn/automating-secure-and-scalable-website-deployment-on-aws-with-amazon-cloudfront-and-aws-cdk/ "AWS APN Blog: Automating Website Deployment with CDK"
[10]: https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-cdk-layers/layer-3.html "AWS Prescriptive Guidance: Layer 3 Constructs"
[11]: https://xebia.com/blog/secure-s3-bucket-constructs-with-cdk-version-2/ "Xebia: Secure S3 Bucket Constructs with CDK v2"
[12]: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.Bucket.html "AWS CDK v2: S3 Bucket Class Docs"
[13]: https://github.com/aws/aws-cdk/issues/10969 "GitHub Issue: Enforce AWS Foundational Security Best Practice"
[14]: https://signiance.com/aws-s3-security-best-practices-a-complete-guide-for-2025/ "Signiance: AWS S3 Security Best Practices 2025"
[15]: https://docs.aws.amazon.com/solutions/latest/constructs/aws-cloudfront-s3.html "AWS Solutions Constructs: aws-cloudfront-s3"
[16]: https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-cloudfront-s3/lib/index.ts "aws-solutions-constructs CloudFrontToS3 source"
[17]: https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html "AWS CDK v2 Best Practices Guide"
[18]: https://github.com/aws/aws-cdk/releases "AWS CDK Releases"
[19]: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront.ResponseHeadersPolicy.html "CDK ResponseHeadersPolicy Docs"
[20]: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront_origins.S3BucketOrigin.html "CDK S3BucketOrigin Class Docs"
[21]: https://github.com/aws/aws-cdk/issues/31360 "GitHub Issue: S3BucketOrigin.withOriginAccessControl incompatible with autoDeleteObjects"
[22]: https://github.com/aws/aws-cdk/issues/34279 "GitHub Issue: withOriginAccessControl does not add policy to new bucket when switched"

## Research Log

---

### Search: "AWS CDK v2 Origin Access Control OAC vs OAI static site S3 CloudFront 2025 2026"

- **OAC is now the recommended approach**, replacing OAI for securing CloudFront distributions with S3 origins ([AWS Blog][1], [AWS Docs][5])
- **OAC advantages over OAI**: short-term credentials, frequent credential rotations, resource-based policies, supports SSE-KMS, supports all HTTP methods (GET, PUT, POST, PATCH, DELETE, OPTIONS, HEAD), works in all AWS regions including opt-in regions ([AWS Docs][5])
- **OAI limitations**: does not support SSE-KMS, opt-in regions, or dynamic requests (PUT, POST, DELETE) to S3 ([AWS Docs][5])
- **CDK L2 construct for OAC was launched** in late 2024 -- the `S3Origin` class is **deprecated** in favor of `S3BucketOrigin.withOriginAccessControl()` ([AWS Blog][1], [CDK Origins Docs][2])
- **Migration path**: Replace `S3Origin` with `S3BucketOrigin.withOriginAccessControl()` which automatically creates and sets up OAC. Recommended to perform upgrade across multiple deployments to avoid downtime ([AWS Blog][1])
- **`S3StaticWebsiteOrigin`** is the new class for static website S3 origins (as opposed to standard S3 bucket origins) ([CDK Origins Docs][2])
- The RFC for the OAC L2 construct is documented at ([CDK RFC 0617][4])

**Follow-up questions:** What does the actual CDK code look like for S3BucketOrigin.withOriginAccessControl()? What about L3 constructs that bundle CloudFront + S3 + ACM + Route53?

---

### Fetch: AWS CDK v2 CloudFront Origins Module Docs

Full code examples from the official CDK docs ([CDK Origins Docs][2]):

**Basic OAC setup (recommended):**
```typescript
const myBucket = new s3.Bucket(this, 'myBucket');
new cloudfront.Distribution(this, 'myDist', {
  defaultBehavior: { origin: origins.S3BucketOrigin.withOriginAccessControl(myBucket) },
});
```

**Custom OAC with signing config:**
```typescript
const oac = new cloudfront.S3OriginAccessControl(this, 'MyOAC', {
  signing: cloudfront.Signing.SIGV4_NO_OVERRIDE
});
const s3Origin = origins.S3BucketOrigin.withOriginAccessControl(myBucket, {
  originAccessControl: oac
});
```

**OAC with SSE-KMS encryption (key feature OAI cannot do):**
```typescript
const myKmsKey = new kms.Key(this, 'myKMSKey');
const myBucket = new s3.Bucket(this, 'mySSEKMSEncryptedBucket', {
  encryption: s3.BucketEncryption.KMS,
  encryptionKey: myKmsKey,
  objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
});
new cloudfront.Distribution(this, 'myDist', {
  defaultBehavior: {
    origin: origins.S3BucketOrigin.withOriginAccessControl(myBucket)
  },
});
```

**Legacy OAI (deprecated):**
```typescript
new cloudfront.Distribution(this, 'myDist', {
  defaultBehavior: {
    origin: origins.S3BucketOrigin.withOriginAccessIdentity(myBucket)
  },
});
```

- **S3 Object Ownership must be "Bucket owner enforced"** (default) when using OAC with S3 ([CDK Origins Docs][2])
- **`S3BucketOrigin.withBucketDefaults()`** is available for no access control (public bucket) ([CDK Origins Docs][2])
- **`originAccessLevels`** parameter allows fine-grained control: READ, READ_VERSIONED, WRITE, DELETE, LIST ([CDK Origins Docs][2])

---

### Search: "AWS CDK L3 construct static site CloudFront S3 ACM Route53 all-in-one 2025 2026"

- **No official AWS L3 construct** for the full static site stack (CloudFront + S3 + ACM + Route53) ships with aws-cdk-lib ([AWS Prescriptive Guidance][10])
- **AWS provides an official example** in aws-cdk-examples repo: a `StaticSite` custom construct that combines S3, CloudFront, ACM, and Route53 ([AWS CDK Examples][7])
- **Community L3 construct**: `@ukautz/aws-cdk-static-website` implements S3 + CloudFront + ACM + Route53 with HTTPS enforcement ([Community L3][8])
- AWS Prescriptive Guidance describes L3 constructs as "patterns" -- purpose-built constructs that provision multiple L2 constructs for a specific use case ([AWS Prescriptive Guidance][10])

**Follow-up questions:** Need to check the aws-cdk-examples static site code for current patterns. Also need to research S3 security best practices (bucket policies, encryption) and CDK v2 changes since 2024.

---

### Fetch: AWS CDK Examples Static Site TypeScript + Search: S3 Security Best Practices

**Complete official example construct** from aws-cdk-examples repo ([AWS CDK Examples][7]) -- key highlights:
- Uses `S3BucketOrigin.withOriginAccessControl(siteBucket)` (modern OAC approach)
- S3 bucket configured with `blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL` and `publicReadAccess: false`
- ACM certificate with DNS validation via Route53: `acm.CertificateValidation.fromDns(zone)`
- CloudFront distribution with `minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021`
- Route53 ARecord with `targets.CloudFrontTarget(distribution)`
- `s3deploy.BucketDeployment` with `distributionPaths: ['/*']` for cache invalidation
- Viewer protocol policy set to `REDIRECT_TO_HTTPS`
- Compression enabled via `compress: true`

**S3 Security Best Practices for CDK v2** ([Xebia][11], [CDK S3 Docs][12], [Security Guide][14]):
- **Block all public access**: `blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL` -- recommended for all buckets, aligns with AWS Security Hub control S3.8
- **Enforce SSL**: `enforceSSL: true` property enforces HTTPS for all requests, part of AWS Foundational Security Best Practices
- **Encryption**: SSE-S3 (default) or SSE-KMS. For KMS, use `bucketKeyEnabled: true` to reduce KMS API costs by using an intermediary S3 bucket key
- **Versioning**: Enable for data protection, especially if content needs rollback capability
- **Access logging**: Enable server access logs with `serverAccessLogsPrefix`
- AWS Foundational Security Best Practices audit checks for: public access blocked, SSL enforced, encryption enabled, versioning considered ([GitHub Issue][13])

**Follow-up questions:** What CDK v2 changes have happened since 2024? Are there new CDK patterns or constructs for static sites? What about aws-solutions-constructs library?

---

### Search: "aws-solutions-constructs CloudFront S3 static site construct 2025 2026" + Fetch: source code

**AWS Solutions Constructs `CloudFrontToS3`** is an official AWS-maintained L3 pattern construct ([AWS Solutions Constructs Docs][15], [Source][16]):

- **Uses OAC, not OAI** -- the source code explicitly "attaches the OriginAccessControl to the CloudFront Distribution, and removes the OriginAccessIdentity" ([Source][16])
- **Security defaults enabled by default:**
  - HTTP security headers automatically injected in all responses (`insertHttpSecurityHeaders` defaults to `true`)
  - S3 bucket policy grants only `s3:GetObject` on objects and `s3:ListBucket` on the bucket, restricted to the specific CloudFront distribution ARN
  - Access logging for both S3 and CloudFront buckets
- **KMS support**: Handles the circular dependency problem when using KMS encryption via a custom resource ([Source][16])
- **Provisions**: CloudFront distribution, S3 content bucket (or accepts existing), S3 logging bucket, CloudFront logging bucket
- **Does NOT include**: ACM certificate or Route53 -- it's purely CloudFront + S3
- Package: `@aws-solutions-constructs/aws-cloudfront-s3`

**Also found**: `aws-cloudfront-oai-s3` is an older construct that still exists but uses OAI (legacy approach)

---

### Search: "AWS CDK v2 changes new features 2025 2026 static site deployment best practices"

- **CDK v2 Best Practices guide** is maintained at AWS docs ([Best Practices][17])
- Key general CDK best practices: organize into logical units (constructs), use stacks as deployment units, separate concerns
- **No major new static-site-specific constructs** have been added to `aws-cdk-lib` core beyond the OAC L2 constructs already documented
- CDK releases tracked at ([CDK Releases][18])
- The major recent change for static site hosting was the OAC L2 construct release and deprecation of `S3Origin`

---

### Search: "AWS CDK CloudFront ResponseHeadersPolicy security headers static site best practice 2025"

**ResponseHeadersPolicy** is the CDK construct for adding security headers to CloudFront responses ([ResponseHeadersPolicy Docs][19]):

- **Pre-built managed policies available**: `ResponseHeadersPolicy.SECURITY_HEADERS` is a built-in AWS-managed policy
- **Custom security headers** configurable: Strict-Transport-Security (HSTS), Content-Type-Options, X-Frame-Options, Content-Security-Policy, Referrer-Policy
- **HSTS best practice**: max-age of at least 31536000 seconds (1 year), include `includeSubDomains`
- **X-Frame-Options**: set to "DENY" or "SAMEORIGIN" to prevent clickjacking
- **X-Content-Type-Options**: "nosniff" to block MIME type confusion
- CDK validates header syntax and values automatically

---

### Search: "AWS CDK v2 S3BucketOrigin withOriginAccessControl bucket policy automatic what gets created"

**What `S3BucketOrigin.withOriginAccessControl()` creates automatically** ([S3BucketOrigin Docs][20], [AWS Blog][1]):

1. **OAC resource** (`AWS::CloudFront::OriginAccessControl`) -- created automatically if not provided
2. **S3 bucket policy** -- automatically updated with statement granting CloudFront access to the bucket
3. **KMS key policy** (if applicable) -- automatically updated to grant OAC permission to use the KMS key for SSE-KMS encrypted buckets
4. **Distribution origin config** -- sets `OriginAccessControlId` on the distribution origin

**Known issues:**
- `S3BucketOrigin.withOriginAccessControl` is **incompatible with `autoDeleteObjects: true`** on the bucket -- the custom resource Lambda used for auto-delete cannot access the bucket because OAC restricts access to CloudFront only ([GitHub Issue][21])
- There's a reported issue where switching from OAI to OAC on an existing bucket may not correctly add the new policy ([GitHub Issue][22])
- Workaround for `autoDeleteObjects`: set `removalPolicy: RemovalPolicy.DESTROY` without `autoDeleteObjects`, and manually handle cleanup, or use a separate Lambda with explicit bucket permissions
