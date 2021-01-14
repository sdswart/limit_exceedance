import sys, os
import json

#boto3 makes use of the following environment variables:
#AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_DEFAULT_REGION

def parse_json(data):
    if data:
        try:
            return json.loads(data)
        except:
            return json.loads(f'"{data}"')

class CONFIG(object):
    VERSION=os.environ.get('VERSION',2.0)
    EXTRA_RETURN_ARGS=parse_json(os.environ.get('EXTRA_RETURN_ARGS'))
    AWS_DEFAULT_REGION=os.environ.get('AWS_DEFAULT_REGION','us-east-1')
    BUCKET_NAME=os.environ.get('BUCKET_NAME')
    OBJECT_PREFIX=os.environ.get('OBJECT_PREFIX','').replace('\\','/')
    if OBJECT_PREFIX.endswith('/'):
        OBJECT_PREFIX=OBJECT_PREFIX[:-1]
    API_USERNAME=os.environ.get('API_USERNAME')
    API_PASSWORD=os.environ.get('API_PASSWORD')
    API_URL=os.environ.get('API_URL')
    USE_S3=False if BUCKET_NAME is None else os.environ.get('USE_S3','false').lower()=='true'
    DELETE_AFTER_COMPLETION=os.environ.get('DELETE_AFTER_COMPLETION','false').lower()=='true'

    RETURN_METHOD='storage' if API_USERNAME is None or API_PASSWORD is None or API_URL is None else 'api'

config=CONFIG()
