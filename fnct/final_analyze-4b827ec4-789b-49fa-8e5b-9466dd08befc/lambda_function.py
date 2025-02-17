import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import uuid
import zipfile
from groq import Groq
import urllib.parse
from io import BytesIO

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: final_analyze**")
    # print(dir(groq))
    
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

    groq_api = configur.get('groq', 'api')
    
    bucketkey = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    #
    # download ZIP from S3 to LOCAL file system:
    #
    print("**DOWNLOADING '", bucketkey, "'**")

    local_zip = "/tmp/data.zip"
    local_txt = "/tmp/data.txt"

    
    bucket.download_file(bucketkey, local_zip)

    try:
      # Open the ZIP file
      with zipfile.ZipFile(local_zip, 'r') as zipf:
        for file_name in zipf.namelist():
          file_data = zipf.read(file_name)
          base64_string = base64.b64encode(file_data).decode("utf-8")

          print(f"Extracted Base64 for file")
    except Exception as e:
        print(f"Error opening ZIP file {zip_filename}: {e}")

    print(file_name)

    client = Groq(api_key = groq_api)
    chat_completion = client.chat.completions.create(
      messages=[
        {
          "role": "user",
          "content": [
              {"type": "text", "text": "Describe the contents of this image in detail."},
              {
                  "type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_string}",
                  },
              },
          ],
        }
      ],
      model="llama-3.2-11b-vision-preview",
      max_tokens=150,
    )


    
    outfile = open(local_txt, "w")
    outfile.write(chat_completion.choices[0].message.content)
    outfile.close()


    print("status change")
    sql= """
        UPDATE images
        SET status = 'analyzed'
        WHERE imageUUID = %s;
      """
    
    print(bucketkey.split('/')[-1][-4])
    datatier.perform_action(dbConn, sql, [bucketkey.split('/')[-1][:-4]])




    # #
    # # write zip to s3
    # #
    # print("**Uploading local zip to S3**")
    

    
    
    print("S3 bucketkey:", bucketkey)

    bucket.upload_file(local_txt, 
                  bucketkey[:-4] + '.txt', 
                  ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': 'application/txt'
                  })

    print("**DONE**")
    
    return {
      'statusCode': 200,
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
