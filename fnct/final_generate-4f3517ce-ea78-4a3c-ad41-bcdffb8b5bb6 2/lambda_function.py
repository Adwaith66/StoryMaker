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
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak, Image, Spacer
from reportlab.lib.utils import ImageReader
styles = getSampleStyleSheet ()
styleN = styles['Normal']
styleH = styles['Heading1']
story = []

from io import BytesIO

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: final_generate**")


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
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    
    if "jobid" in event:
      jobid = event["jobid"]
    elif "pathParameters" in event:
      if "jobid" in event["pathParameters"]:
        jobid = event["pathParameters"]["jobid"]
      else:
        raise Exception("requires jobid parameter in pathParameters")
    else:
        raise Exception("requires jobid parameter in event")

    sql = "SELECT * FROM jobs WHERE jobid = %s;"
    
    row = datatier.retrieve_one_row(dbConn, sql, [jobid])
    
    if row == (): 
      print("**No such jobid, returning...**")
      return {
        'statusCode': 400,
        'body': json.dumps("no such jobid...")
    }

    jobUUID = row[2]

    bucketkey = 'storyapp/' + jobUUID + '/'


    sql =  """
      SELECT * FROM images WHERE jobid = %s ORDER BY imageid;
    """

    t = ""
    i = 0
    UUIDs = []


    rows = datatier.retrieve_all_rows(dbConn, sql, [jobid])
    for row in rows:
      if row[4] != 'analyzed':
        return {
          'statusCode': 500,
          'body': 'wait for all images to be analyzed'
        }

      else:
        print(bucketkey + row[3] + '.txt')
        bucket.download_file(bucketkey + row[3] + '.txt', '/tmp/' + row[3] + ".txt")
        bucket.download_file(bucketkey + row[3] + '.zip', '/tmp/' + row[3] + ".zip")
        zip_i = zipfile.ZipFile('/tmp/' + row[3] + ".zip", 'r')
        zip_i.extract(zip_i.namelist()[0], '/tmp/')


        UUIDs.append('/tmp/' + row[3] + ".jpg")
        f = open('/tmp/' + row[3] + ".txt", 'r', encoding='utf-8')
        t += " This is image " + str(i) +  " " + f.read()
        i += 1

    print("HIAHSDFIHASDF" , i)

    print(os.listdir('/tmp'))

    client = Groq(api_key = groq_api)
    chat_completion = client.chat.completions.create(
      messages=[
        {
          "role": "user",
          "content": [
              {"type": "text", "text": f"""
                I will provide a series of descriptions that collectively outline a narrative story. 
                Each description represents a different part of the story, and I want you to write a seamless narrative connecting them. 
                Do not refer to any images directly, and do not include any explanations or comments beyond the story. 
                Focus purely on creating a cohesive narrative, pay special attention to ensring logical transitions between descriptions.
                Respond with the final story text with no additional text or references.
                """  + t},
          ],
        }
      ],
      model="llama-3.2-11b-vision-preview",
    )
    print(chat_completion.choices[0].message.content)

    chat_completion = client.chat.completions.create(
      messages=[
        {
          "role": "user",
          "content": [
              {"type": "text", "text": f"""I will provide a narrative story, and I want it to be seperated into EXACTLY {i-1} sections logically by inserting {i-1} "|". There cannot be any variance in the number of sections. DO NOT ADD OR REMOVE ANY CONTENT, SIMPLY SEPARATE IT.
                """  + chat_completion.choices[0].message.content},
          ],
        }
      ],
      model="llama-3.2-11b-vision-preview",
    )


    print(chat_completion.choices[0].message.content)
    stories =chat_completion.choices[0].message.content.split('|')


    output_file = "/tmp/output.pdf"

    while len(stories) < i:
      stories.append("")
      
    for i,v in enumerate(UUIDs):
      print("INDEX", i)
      img = ImageReader(v)
      image_width, image_height = img.getSize()
      
      max_width = letter[0] - 200
      max_height = letter[1] - 100
      scale = min(max_width / image_width, (max_height / 2) / image_height)  
      new_width = image_width * scale
      new_height = image_height * scale


      story.append(Paragraph(stories[i] +'\n\n', styleN))
      story.append(Spacer(1, 12))
      story.append(Image(v, width=new_width, height=new_height))
      story.append(Spacer(1, 12))


    doc = SimpleDocTemplate(output_file,pagesize = letter)
    doc.build(story)
      
    bucket.upload_file(output_file, 
                  bucketkey+'story.pdf' , 
                  ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': 'application/pdf'
                  })

    sql= """
    UPDATE jobs
    SET status = 'viewable'
    WHERE jobid = %s;
    """
    
    datatier.perform_action(dbConn, sql, [jobid])
    url = "https://photoapp-adwaithsreekumar-nu-cs310.s3.us-east-2.amazonaws.com/storyapp/" + jobUUID + '/story.pdf'
    print(bucketname)
    
    return {
      'statusCode': 200,
      'headers': {'Content-Type': 'application/json'},
      'body': f'{{"downloadUrl": "{url}"}}'    
      }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
