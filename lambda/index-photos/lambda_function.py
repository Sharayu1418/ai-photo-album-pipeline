import json
import boto3
import urllib.parse
from datetime import datetime
import os
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import urllib.request

def get_aws_auth():
    """Get AWS credentials for signing requests."""
    session = boto3.Session()
    credentials = session.get_credentials()
    return credentials

def signed_request(method, url, data=None, headers=None, service='es', region='us-east-1'):
    """Make a signed request to AWS services."""
    if headers is None:
        headers = {}
    
    credentials = get_aws_auth()
    
    # Create the request
    if data:
        data_bytes = data.encode('utf-8') if isinstance(data, str) else data
    else:
        data_bytes = None
    
    request = AWSRequest(method=method, url=url, data=data_bytes, headers=headers)
    
    # Sign the request
    SigV4Auth(credentials, service, region).add_auth(request)
    
    # Make the actual request
    req = urllib.request.Request(
        url,
        data=data_bytes,
        method=method,
        headers=dict(request.headers)
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_body}")
        raise

def lambda_handler(event, context):
    """
    Lambda function to index photos uploaded to S3.
    Triggered by S3 PUT events.
    Uses Rekognition to detect labels and stores metadata in OpenSearch.
    """
    print("Index Photos Lambda triggered")
    print(f"Event: {json.dumps(event)}")
    
    s3 = boto3.client('s3')
    rekognition = boto3.client('rekognition')
    
    # Get bucket and key from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    print(f"Processing image: {bucket}/{key}")
    
    # Detect labels using Rekognition
    labels = []
    try:
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=10,
            MinConfidence=70
        )
        labels = [label['Name'].lower() for label in response['Labels']]
        print(f"Rekognition labels: {labels}")
    except Exception as e:
        print(f"Rekognition error: {e}")
    
    # Get custom labels from S3 metadata
    try:
        head_response = s3.head_object(Bucket=bucket, Key=key)
        metadata = head_response.get('Metadata', {})
        print(f"S3 Metadata: {metadata}")
        
        custom_labels_str = metadata.get('customlabels', '') or metadata.get('customLabels', '')
        
        if custom_labels_str:
            custom_labels = [l.strip().lower() for l in custom_labels_str.split(',') if l.strip()]
            labels.extend(custom_labels)
            print(f"Custom labels: {custom_labels}")
    except Exception as e:
        print(f"Error getting metadata: {e}")
    
    # Remove duplicates
    labels = list(set(labels))
    
    # Create document for OpenSearch
    document = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.now().isoformat(),
        "labels": labels
    }
    
    print(f"Document to index: {json.dumps(document)}")
    
    # Index to OpenSearch with signed request
    opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT', 'https://search-photos-5q7clr3fduwyh4smyqpjz3xrcm.us-east-1.es.amazonaws.com')
    
    if opensearch_endpoint:
        try:
            doc_id = key.replace('/', '_').replace(' ', '_')
            url = f"{opensearch_endpoint}/photos/_doc/{doc_id}"
            
            result = signed_request(
                method='PUT',
                url=url,
                data=json.dumps(document),
                headers={'Content-Type': 'application/json'}
            )
            print(f"OpenSearch response: {result}")
        except Exception as e:
            print(f"OpenSearch indexing error: {e}")
            raise e
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Photo indexed successfully',
            'bucket': bucket,
            'key': key,
            'labels': labels
        })
    }
