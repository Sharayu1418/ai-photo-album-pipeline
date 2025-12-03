import json
import boto3
import urllib.request
import os

def lambda_handler(event, context):
    """
    Lambda function to search photos based on natural language queries.
    Uses Lex V2 for query disambiguation and OpenSearch for searching.
    """
    print(f"Search Photos Lambda triggered")
    print(f"Event: {json.dumps(event)}")
    
    # Get query from API Gateway event
    query = ""
    if 'queryStringParameters' in event and event['queryStringParameters']:
        query = event['queryStringParameters'].get('q', '')
    
    print(f"Query: {query}")
    
    if not query:
        return build_response({'results': []})
    
    # Use Lex V2 to disambiguate the query
    lex_client = boto3.client('lexv2-runtime', region_name='us-east-1')
    bot_id = os.environ.get('LEX_BOT_ID', '9TWNFOOXWF')
    bot_alias_id = os.environ.get('LEX_BOT_ALIAS_ID', 'TSTALIASID')
    
    keywords = []
    try:
        lex_response = lex_client.recognize_text(
            botId=bot_id,
            botAliasId=bot_alias_id,
            localeId='en_US',
            sessionId='user-session-' + context.aws_request_id,
            text=query
        )
        print(f"Lex response: {json.dumps(lex_response, default=str)}")
        
        # Extract slots from Lex response
        if 'sessionState' in lex_response and 'intent' in lex_response['sessionState']:
            intent = lex_response['sessionState']['intent']
            slots = intent.get('slots', {})
            
            if slots:
                for slot_name, slot_value in slots.items():
                    if slot_value:
                        # Handle Lex V2 slot structure
                        if 'value' in slot_value:
                            interpreted = slot_value['value'].get('interpretedValue', '')
                            if interpreted:
                                keywords.append(interpreted.lower())
                        # Handle list of values
                        elif 'values' in slot_value:
                            for val in slot_value['values']:
                                if 'value' in val:
                                    interpreted = val['value'].get('interpretedValue', '')
                                    if interpreted:
                                        keywords.append(interpreted.lower())
        
        print(f"Keywords from Lex: {keywords}")
    except Exception as e:
        print(f"Lex error: {e}")
    
    # Fallback: if no keywords from Lex, parse query manually
    if not keywords:
        # Remove common words and extract meaningful keywords
        stop_words = {'show', 'me', 'find', 'search', 'for', 'photos', 'pictures', 'images', 
                      'with', 'of', 'the', 'a', 'an', 'and', 'or', 'in', 'them', 'please'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
    
    print(f"Final keywords: {keywords}")
    
    if not keywords:
        return build_response({'results': []})
    
    # Search OpenSearch
    opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT', 'https://search-photos-5q7clr3fduwyh4smyqpjz3xrcm.us-east-1.es.amazonaws.com')
    photos_bucket = os.environ.get('PHOTOS_BUCKET', 'album-photos-bucket')
    
    results = search_opensearch(opensearch_endpoint, keywords, photos_bucket)
    
    return build_response({'results': results})


def search_opensearch(endpoint, keywords, default_bucket):
    """Search OpenSearch for photos matching the keywords."""
    results = []
    
    if not endpoint or not keywords:
        return results
    
    try:
        # Build search query - match any of the keywords in labels
        should_clauses = [{"match": {"labels": keyword}} for keyword in keywords]
        search_query = {
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            },
            "size": 50
        }
        
        url = f"{endpoint}/photos/_search"
        data = json.dumps(search_query).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            search_results = json.loads(response.read().decode('utf-8'))
            print(f"OpenSearch results: {json.dumps(search_results)}")
            
            hits = search_results.get('hits', {}).get('hits', [])
            
            for hit in hits:
                source = hit.get('_source', {})
                bucket = source.get('bucket', default_bucket)
                key = source.get('objectKey', '')
                
                if key:
                    photo_url = f"https://{bucket}.s3.amazonaws.com/{key}"
                    results.append({
                        'url': photo_url,
                        'labels': source.get('labels', []),
                        'objectKey': key,
                        'bucket': bucket
                    })
    except urllib.error.HTTPError as e:
        print(f"OpenSearch HTTP error: {e.code} - {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"Error body: {error_body}")
    except Exception as e:
        print(f"OpenSearch search error: {e}")
    
    return results


def build_response(body):
    """Build HTTP response with CORS headers."""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-amz-meta-customLabels',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(body)
    }

