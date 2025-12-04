# AI Photo Album Pipeline

An intelligent photo album web application that leverages AWS services to enable natural language photo search. Upload your photos and search for them using conversational queries like "show me photos with dogs" or "find pictures from the beach."

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Deployment](#deployment)
- [Usage](#usage)
- [API Reference](#api-reference)
- [AWS Resource Naming](#aws-resource-naming)
- [CI/CD Pipeline](#cicd-pipeline)

## Features

- **Natural Language Search**: Search photos using everyday language powered by Amazon Lex V2
- **Automatic Image Labeling**: Photos are automatically analyzed and tagged using Amazon Rekognition
- **Scalable Storage**: Secure photo storage with Amazon S3
- **Full-Text Search**: Fast and relevant search results powered by Amazon OpenSearch
- **Serverless Architecture**: Cost-effective, auto-scaling backend using AWS Lambda
- **CI/CD Automation**: Fully automated deployment pipelines with AWS CodePipeline

## Architecture

```
                                    +------------------+
                                    |    Frontend      |
                                    |   (S3 Static)    |
                                    +--------+---------+
                                             |
                                             v
+------------------+              +----------+----------+
|   Lex V2 Bot     |<------------>|    API Gateway     |
| (PhotoSearchBot) |              +----------+----------+
+------------------+                         |
                                    +--------+--------+
                                    |                 |
                              +-----v-----+     +-----v-----+
                              |  Search   |     |   Index   |
                              |  Lambda   |     |  Lambda   |
                              +-----+-----+     +-----+-----+
                                    |                 |
                              +-----v-----+     +-----v-----+
                              | OpenSearch|     |Rekognition|
                              |  Domain   |     |  Service  |
                              +-----------+     +-----+-----+
                                    ^                 |
                                    |                 v
                                    |           +-----+-----+
                                    +-----------+  Photos   |
                                                |S3 Bucket  |
                                                +-----------+
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| Amazon S3 | Frontend hosting and photo storage |
| AWS Lambda | Photo indexing and search functionality |
| Amazon API Gateway | REST API endpoints |
| Amazon Rekognition | Automatic image label detection |
| Amazon OpenSearch | Photo metadata indexing and full-text search |
| Amazon Lex V2 | Natural language query processing |
| AWS CodePipeline | CI/CD automation |
| AWS CloudFormation | Infrastructure as Code |

## Project Structure

```
ai-photo-album-pipeline/
├── cloudformation/          # CloudFormation templates for AWS resources
├── frontend/                # Static web application (HTML, CSS, JavaScript)
├── lambda/                  # Lambda function source code (Python)
├── buildspec-frontend.yml   # CodeBuild spec for frontend deployment
├── buildspec-lambda.yml     # CodeBuild spec for Lambda deployment
├── pipeline-cloudformation.yaml  # CI/CD pipeline infrastructure
└── README.md
```

## Prerequisites

Before deploying this application, ensure you have the following:

### AWS Resources (Manual Setup Required)

1. **Amazon OpenSearch Domain**
   - Domain name: `photos`
   - Note the endpoint URL for configuration

2. **Amazon Lex V2 Bot**
   - Bot name: `PhotoSearchBot`
   - Create an alias: `TestBotAlias`
   - Note the Bot ID and Alias ID

### Local Development Requirements

- AWS CLI v2 installed and configured
- Python 3.9+
- Node.js 16+ (for frontend development)
- Git

### AWS Permissions

Ensure your AWS credentials have permissions for:
- S3 (bucket creation, object management)
- Lambda (function creation, execution)
- API Gateway (API creation, deployment)
- Rekognition (image analysis)
- OpenSearch (domain access)
- Lex (bot invocation)
- CloudFormation (stack management)
- CodePipeline (pipeline management)
- IAM (role creation)

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/Sharayu1418/ai-photo-album-pipeline.git
cd ai-photo-album-pipeline
```

2. **Configure AWS CLI**

```bash
aws configure
```

3. **Set up environment variables**

Create a `.env` file or export the following variables:

```bash
export AWS_ACCOUNT_ID=<your-account-id>
export AWS_REGION=<your-region>
export OPENSEARCH_ENDPOINT=<your-opensearch-endpoint>
export LEX_BOT_ID=<your-lex-bot-id>
export LEX_BOT_ALIAS_ID=<your-lex-alias-id>
```

## Deployment

### Option 1: CloudFormation Deployment

Deploy the entire infrastructure using CloudFormation:

```bash
aws cloudformation deploy \
  --template-file pipeline-cloudformation.yaml \
  --stack-name ai-photo-album-pipeline \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    OpenSearchEndpoint=$OPENSEARCH_ENDPOINT \
    LexBotId=$LEX_BOT_ID \
    LexBotAliasId=$LEX_BOT_ALIAS_ID
```

### Option 2: Manual Deployment

1. **Deploy Lambda Functions**

```bash
cd lambda
zip -r index-photos.zip index-photos/
zip -r search-photos.zip search-photos/

aws lambda create-function \
  --function-name album-index-photos \
  --runtime python3.9 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://index-photos.zip \
  --role <lambda-execution-role-arn>

aws lambda create-function \
  --function-name album-search-photos \
  --runtime python3.9 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://search-photos.zip \
  --role <lambda-execution-role-arn>
```

2. **Deploy Frontend**

```bash
cd frontend
aws s3 sync . s3://album-frontend-bucket-$AWS_ACCOUNT_ID --delete
```

## Usage

### Uploading Photos

1. Navigate to the web application
2. Click the upload button or drag and drop photos
3. Optionally add custom labels during upload
4. Photos are automatically processed and indexed

### Searching Photos

Use natural language queries to find your photos:

- "Show me photos with dogs"
- "Find pictures of people"
- "Search for beach photos"
- "Show me images with cars and trees"

The application uses Amazon Lex to understand your query and returns relevant results from the indexed photos.

## API Reference

### Upload Photo

```
PUT /upload/{bucket}/{filename}
```

**Headers:**
- `Content-Type`: image/jpeg, image/png, etc.
- `x-amz-meta-customLabels`: (optional) comma-separated custom labels

**Response:** `200 OK` on success

### Search Photos

```
GET /search?q={query}
```

**Parameters:**
- `q`: Natural language search query

**Response:**
```json
{
  "results": [
    {
      "url": "https://...",
      "labels": ["dog", "outdoor", "grass"]
    }
  ]
}
```

## AWS Resource Naming

All resources follow the `album-` prefix convention:

| Resource | Name |
|----------|------|
| Frontend Bucket | `album-frontend-bucket-{AccountId}` |
| Photos Bucket | `album-photos-bucket-{AccountId}` |
| Index Lambda | `album-index-photos` |
| Search Lambda | `album-search-photos` |
| API Gateway | `album-photo-api` |
| Backend Pipeline | `album-backend-pipeline` |
| Frontend Pipeline | `album-frontend-pipeline` |

## CI/CD Pipeline

The project includes two CodePipeline configurations:

### Backend Pipeline (`album-backend-pipeline`)

Triggered on changes to the `lambda/` directory:
1. Source: GitHub repository
2. Build: Package Lambda functions
3. Deploy: Update Lambda function code

### Frontend Pipeline (`album-frontend-pipeline`)

Triggered on changes to the `frontend/` directory:
1. Source: GitHub repository
2. Build: Process frontend assets
3. Deploy: Sync to S3 frontend bucket

### Build Specifications

- `buildspec-lambda.yml`: Defines the build process for Lambda functions
- `buildspec-frontend.yml`: Defines the build process for frontend assets

## Troubleshooting

### Common Issues

**Photos not being indexed**
- Verify the S3 bucket trigger is configured for the index Lambda
- Check Lambda CloudWatch logs for errors
- Ensure Rekognition permissions are configured

**Search returning no results**
- Verify OpenSearch domain is accessible
- Check that photos have been properly indexed
- Review search Lambda CloudWatch logs

**Lex not understanding queries**
- Ensure the Lex bot is properly trained
- Check that the bot alias is deployed
- Verify Lex permissions in the search Lambda role

## Acknowledgments

- AWS Documentation for service integration guides
- Amazon Rekognition for powerful image analysis capabilities
- Amazon Lex for natural language understanding
