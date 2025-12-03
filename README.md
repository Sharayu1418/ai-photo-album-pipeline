# AI Photo Album Pipeline

An intelligent photo album web application that uses AWS services for natural language photo search.

## Architecture

- **S3**: Frontend hosting + Photo storage
- **Lambda**: Photo indexing + Search functionality  
- **API Gateway**: REST API endpoints
- **Rekognition**: Automatic image label detection
- **OpenSearch**: Photo metadata indexing and search
- **Lex V2**: Natural language query processing
- **CodePipeline**: CI/CD automation

## Resource Names (album prefix)

| Resource | Name |
|----------|------|
| Frontend Bucket | `album-frontend-bucket-{AccountId}` |
| Photos Bucket | `album-photos-bucket-{AccountId}` |
| Index Lambda | `album-index-photos` |
| Search Lambda | `album-search-photos` |
| API Gateway | `album-photo-api` |
| Backend Pipeline | `album-backend-pipeline` |
| Frontend Pipeline | `album-frontend-pipeline` |

## Pre-requisites

Before deployment, ensure you have:
1. **OpenSearch Domain**: `photos` (Endpoint: `https://search-photos-5q7clr3fduwyh4smyqpjz3xrcm.us-east-1.es.amazonaws.com`)
2. **Lex V2 Bot**: `PhotoSearchBot` (ID: `9TWNFOOXWF`)
3. **Lex Alias**: `TestBotAlias` (ID: `TSTALIASID`)
4. **AWS CLI** configured with appropriate permissions

---

## DEPLOYMENT INSTRUCTIONS

### Step 1: Push Code to GitHub

```bash
cd ai-photo-album-pipeline

# Initialize git repository
git init
git add .
git commit -m "Initial commit - Photo Album Application"

# Add remote and push
git remote add origin https://github.com/Sharayu1418/ai-photo-album-pipeline.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Main CloudFormation Stack

This creates: S3 buckets, Lambda functions, API Gateway, IAM roles.

```bash
aws cloudformation create-stack \
  --stack-name album-photo-stack \
  --template-body file://cloudformation/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Wait for stack creation to complete:**
```bash
aws cloudformation wait stack-create-complete --stack-name album-photo-stack --region us-east-1
```

**Get the outputs (API Gateway URL):**
```bash
aws cloudformation describe-stacks --stack-name album-photo-stack --query "Stacks[0].Outputs" --region us-east-1
```

### Step 3: Configure S3 Trigger for Lambda

After the stack is created, add the S3 event trigger:

1. Go to **AWS Console > S3 > album-photos-bucket-{AccountId}**
2. Click **Properties** tab
3. Scroll to **Event notifications** > Click **Create event notification**
4. Configure:
   - **Name**: `IndexPhotosOnUpload`
   - **Event types**: Check `All object create events`
   - **Destination**: Lambda function > Select `album-index-photos`
5. Click **Save changes**

### Step 4: Create OpenSearch Index

Create the `photos` index in OpenSearch:

```bash
curl -X PUT "https://search-photos-5q7clr3fduwyh4smyqpjz3xrcm.us-east-1.es.amazonaws.com/photos" \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": {
      "properties": {
        "objectKey": { "type": "text" },
        "bucket": { "type": "text" },
        "createdTimestamp": { "type": "date" },
        "labels": { "type": "text" }
      }
    }
  }'
```

### Step 5: Update Frontend with API Gateway URL

1. Get your API Gateway URL from Step 2 outputs
2. Edit `frontend/script.js`
3. Replace `YOUR_API_GATEWAY_URL` with your actual URL:

```javascript
const API_BASE_URL = 'https://xxxxxxxx.execute-api.us-east-1.amazonaws.com/prod';
```

### Step 6: Upload Frontend to S3

```bash
# Get your account ID
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# Upload frontend files
aws s3 sync frontend/ s3://album-frontend-bucket-$ACCOUNT_ID/ --region us-east-1
```

### Step 7: Access Your Application

Get the frontend URL:
```bash
aws cloudformation describe-stacks --stack-name album-photo-stack \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendWebsiteURL'].OutputValue" \
  --output text --region us-east-1
```

---

## OPTIONAL: Deploy CodePipeline (CI/CD)

### Step 1: Create GitHub Connection

1. Go to **AWS Console > Developer Tools > Settings > Connections**
2. Click **Create connection**
3. Select **GitHub** > Name: `album-github-connection`
4. Click **Connect to GitHub** and authorize
5. **Copy the Connection ARN**

### Step 2: Deploy Pipeline Stack

```bash
aws cloudformation create-stack \
  --stack-name album-pipeline-stack \
  --template-body file://pipeline-cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=GitHubConnectionArn,ParameterValue=YOUR_CONNECTION_ARN \
  --region us-east-1
```

---

## Testing the Application

### Test Search

1. Open the frontend URL in your browser
2. Type a search query like "show me dogs" or "trees"
3. Results should display matching photos

### Test Upload

1. Click the upload area or drag-and-drop an image
2. Optionally add custom labels (comma-separated)
3. Click "Upload Photo"
4. Wait a few seconds for indexing
5. Search for the labels to find your photo

---

## Troubleshooting

### Lambda Not Triggered by S3
- Verify S3 event notification is configured correctly
- Check Lambda permissions for S3 invoke

### Search Returns Empty
- Verify OpenSearch index exists
- Check Lambda logs in CloudWatch
- Ensure Lex bot is built and deployed

### CORS Errors
- Verify API Gateway CORS settings
- Check S3 bucket CORS configuration

### Upload Fails
- Check API Gateway S3 proxy configuration
- Verify IAM role permissions

---

## Cleanup

To delete all resources:

```bash
# Delete pipelines first (if created)
aws cloudformation delete-stack --stack-name album-pipeline-stack --region us-east-1

# Empty and delete S3 buckets
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
aws s3 rm s3://album-frontend-bucket-$ACCOUNT_ID --recursive
aws s3 rm s3://album-photos-bucket-$ACCOUNT_ID --recursive

# Delete main stack
aws cloudformation delete-stack --stack-name album-photo-stack --region us-east-1
```

