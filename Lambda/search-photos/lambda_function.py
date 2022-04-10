import json
import boto3
import base64
import time
from requests_aws4auth import AWS4Auth
import requests
    
region = 'us-east-1'
esHost="https://search-photos2-2tdnlsvoes6lrz425m54yszgle.us-east-1.es.amazonaws.com"

    
def lambda_handler(event, context):
    print(event)
    query = event['queryStringParameters']["q"] 
    print(query)
    labels = getLabelsFromLex(query)
    
    result = getDataFromES(labels)
    
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        'body': json.dumps(result)
    }
    
def getLabelsFromLex(query):
    client = boto3.client('lexv2-runtime',region_name=region)
    response = client.recognize_text(
		botId='DV8AEPKVSZ',
		botAliasId='ZXKKJK5AQX',
		sessionId="test_session_1",
		localeId='en_US',
		text=query
	)
    
    slots = get_slots(response)
    
    labels = []
    for slot in slots:
        if slots[slot] is not None:
            if 'interpretedValue' in slots[slot]['value']:
                labels.append(slots[slot]['value']['interpretedValue'])
            else:
                labels.append(slots[slot]['value']['originalValue'])
    
    return labels
	

def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']
    
def getDataFromES(labels):
    service = "es"
    index = 'photos'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    url = esHost + '/' + index + '/_search'
    
    imageNames = []
    for label in labels:
        query = {"query": {"match": {"labels": label }}}
        headers = { "Content-Type": "application/json" }
        res = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
        res = res.text
        res = json.loads(res)
        res = res['hits']['hits']
        for hit in res:
            image = hit['_source']['objectKey']
            if image not in imageNames:
                imageNames.append(image)
        
    return { 'imagePaths': imageNames}
	