import json
import boto3
import base64
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import time
from requests_aws4auth import AWS4Auth
import requests


def lambda_handler(event, context):
    print(event)
    s3info=event['Records'][0]['s3']
    bucketname=event['Records'][0]['s3']['bucket']['name']
    image=event['Records'][0]['s3']['object']['key']
    #print(bucketname)
    #print(image)
    s3obj = boto3.client('s3')
    getobj=s3obj.get_object(Bucket=bucketname,Key=image)
    body=getobj['Body'].read().decode('utf-8')
    imagebase64 = base64.b64decode(body)
    
    headobj=s3obj.head_object(Bucket=bucketname,Key=image)
    
    print(headobj['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'])
    
    rkclient = boto3.client('rekognition', region_name='us-east-1')
    #response = rkclient.detect_labels(Image={'S3Object':{'Bucket':bucketname,'Name':image}}, MaxLabels=10,MinConfidence = 85)
    # 'Bytes':image
    response = rkclient.detect_labels(Image={'Bytes':imagebase64}, MaxLabels=10,MinConfidence = 85)
    labels=response['Labels']
    customlabels=[]
    for i in labels:
        customlabels.append(i['Name'])
    timestammp = time.gmtime()
    timecreated = time.strftime("%Y-%m-%dT%H:%M:%S", timestammp)
    customlabels.append(headobj['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'])
    jsonformatfores={
        'objectKey':image,
        'bucket':bucketname,
        'createdTimeStamp':timecreated,
        'labels':customlabels
    }
    print(customlabels)
    essearch="https://search-photos2-2tdnlsvoes6lrz425m54yszgle.us-east-1.es.amazonaws.com"
    region = "us-east-1"
    service = "es"
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    print(awsauth)
    # esClient = Elasticsearch(
    #     hosts=[{'host': essearch, 'port':443}],
    #     use_ssl=True,
    #     http_auth=awsauth,
    #     verify_certs=True,
    #     connection_class=RequestsHttpConnection)
    # print(esClient)
    # temp=esClient.index(index='photos', doc_type='photo', body=jsonformatfores)
    
    essearch=essearch+'/'+'photos'+'/'+'_doc'
    req = requests.post(essearch,auth=awsauth,data=json.dumps(jsonformatfores), headers = { "Content-Type": "application/json" })
    print(req)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
