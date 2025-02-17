
import uuid
import json
import boto3
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: final_add**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'storyapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    if "jobname" in event:
      jobname = event["jobname"]
    elif "pathParameters" in event:
      if "jobname" in event["pathParameters"]:
        jobname = event["pathParameters"]["jobname"]
      else:
        raise Exception("requires jobname parameter in pathParameters")
    else:
        raise Exception("requires jobname parameter in event")
  
    print("**DONE, returning success**")

    sql = """
      INSERT INTO jobs(jobname, jobUUID, status) 
                  VALUES(%s, %s, %s);
    """
  
    datatier.perform_action(dbConn, sql, [jobname, str(uuid.uuid4()), 'declared'])
    
    return {
      'statusCode': 200,
      'body': json.dumps("success")
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
