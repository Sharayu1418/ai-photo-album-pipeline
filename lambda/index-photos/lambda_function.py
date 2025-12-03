import json
import boto3
import urllib.request
import urllib.parse
from datetime import datetime
import os

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
        
        # Try different variations of the custom labels header
        custom_labels_str = metadata.get('customlabels', '') or metadata.get('customLabels', '') or metadata.get('x-amz-meta-customlabels', '')
        
        if custom_labels_str:
            custom_labels = [l.strip().lower() for l in custom_labels_str.split(',') if l.strip()]
            labels.extend(custom_labels)
            print(f"Custom labels: {custom_labels}")
    except Exception as e:
        print(f"Error getting metadata: {e}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_labels = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            unique_labels.append(label)
    labels = unique_labels
    
    # Create document for OpenSearch
    document = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.now().isoformat(),
        "labels": labels
    }
    
    print(f"Document to index: {json.dumps(document)}")
    
    # Index to OpenSearch
    opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT', 'https://search-photos-5q7clr3fduwyh4smyqpjz3xrcm.us-east-1.es.amazonaws.com')
    
    if opensearch_endpoint:
        try:
            # Create a unique document ID from the key
            doc_id = key.replace('/', '_').replace(' ', '_')
            url = f"{opensearch_endpoint}/photos/_doc/{doc_id}"
            
            data = json.dumps(document).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='PUT')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
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

