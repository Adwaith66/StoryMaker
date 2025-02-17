

import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import uuid
import zipfile
from io import BytesIO

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: final_zip**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'storyapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)
    
    bucketname = configur.get('s3', 'bucket_name')
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')
    
    #
    # userid from event: could be a parameter
    # or could be part of URL path ("pathParameters"):
    #
    print("**Accessing event/pathParameters**")
    
    if "jobid" in event:
      jobid = event["jobid"]
    elif "pathParameters" in event:
      if "jobid" in event["pathParameters"]:
        jobid = event["pathParameters"]["jobid"]
      else:
        raise Exception("requires jobid parameter in pathParameters")
    else:
        raise Exception("requires jobid parameter in event")

    if "index" in event:
      index = event["index"]
    elif "pathParameters" in event:
      if "index" in event["pathParameters"]:
        index = event["pathParameters"]["index"]
      else:
        raise Exception("requires index parameter in pathParameters")
    else:
        raise Exception("requires index parameter in event")
        
    print("index:", index)
  
    #
    # the user has sent us two parameters:
    #  1. filename of their file
    #  2. raw file data in base64 encoded string
    #
    # The parameters are coming through web server 
    # (or API Gateway) in the body of the request
    # in JSON format.
    #
    print("**Accessing request body**")
    
    if "body" not in event:
      raise Exception("event has no body")
      
    body = json.loads(event["body"]) # parse the json
    
    if "data" not in body:
      raise Exception("event has a body but no data")

    datastr = body["data"]
    


    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    #
    # first we need to make sure the jobid is valid:
    #
    print("**Checking if jobid is valid**")
    
    sql = "SELECT * FROM jobs WHERE jobid = %s;"
    
    row = datatier.retrieve_one_row(dbConn, sql, [jobid])
    
    if row == (): 
      print("**No such jobid, returning...**")
      return {
        'statusCode': 400,
        'body': json.dumps("no such jobid...")
      }
    
    print(row)
    
    jobUUID = row[2]
    
    #
    # at this point the user exists, so safe to upload to S3:
    #
    # bytes = base64.b64decode(base64_bytes) # base64 bytes -> raw bytes

    imageUUID = str(uuid.uuid4())

    path = '/tmp/' + imageUUID + ".zip"

    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        try:
            # Decode Base64 string
            image_data = base64.b64decode(datastr)
            # Write image data to the ZIP file with the specified filename
            zipf.writestr(imageUUID + '.jpg', image_data)
        except Exception as e:
            print(f"Error processing {imageUUID}: {e}")

    print(os.listdir('/tmp'))
    #
    # write zip to s3
    #
    print("**Uploading local zip to S3**")
    

    
    bucketkey = 'storyapp/' + jobUUID + '/' + imageUUID + '.zip'
    
    print("S3 bucketkey:", bucketkey)

    
    print("**Adding jobs row to database**")
    
    sql = """
      INSERT INTO images(jobid, imageindex, imageUUID, status)
                  VALUES(%s, %s, %s, %s);
    """
  
    datatier.perform_action(dbConn, sql, [jobid, index, imageUUID, 'declared'])


    #
    # now that DB is updated, let's upload to S3
    #
    print("**Uploading data file to S3**")


    bucket.upload_file(path, 
                      bucketkey, 
                      ExtraArgs={
                        'ACL': 'public-read',
                        'ContentType': 'application/zip'
                      })
    
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE**")
    
    return {
      'statusCode': 200,
      'body': json.dumps(str(jobid))
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
