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
1. **OpenSearch Domain**: `photos` (Endpoint)
2. **Lex V2 Bot**: `PhotoSearchBot` (ID)
3. **Lex Alias**: `TestBotAlias` (ID)
4. **AWS CLI** configured with appropriate permissions
