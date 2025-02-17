****Setting Up Server****

This server uses the AWS Lambda Functions and API Endpoints. To properly set it up, three layers are required: one for pymysql, reportlab, and 
groq. All lambda functions will use the pymysql layer, the final-analyze and final-generate functions use groq, and the final generate function
also uses reportlab. The final-analyze and final-generate must use a Python 3.9 runtime, while the others can use 3.12.

Once these layers and lambda functions have been uploaded, a trigger can be applied to final-analyze. Have the function
run whenever a .zip file is uploaded to s3. The rest of the functions are ran by using an API gateway:
There are 5 API Endpoints, which are as follows:
POST: /addjob/{jobname} - final_addjob
GET: /images - final_images
GET: /jobs - final_jobs
POST: /zip/{jobid}/{index} - final_zip
GET: /generate/{jobid} - final_generate

Now that all the lambda functions are set up, simply build and run the Docker container. After which, the file main.py can be ran to interact
with the server. # StoryMaker
