****Overview****
The StoryApp workflow begins when a user creates a new job. Jobs have names, statuses, and
are used to contain the images that will be used in one’s story. After creating a job, the individual
uploads any number of local images into the client-side application. Once they are satisfied, the
server asynchronously processes all these images in order to determine an accurate description of
them using llama-3.211b. In this process, the images are also compressed and stored in S3.
After all the images are processed, the user can generate a story; this results in the creation of a
narrative that combines together the visual elements the user added with a story. These are
combined together in a pdf, which is downloaded to the user’s directory locally



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

