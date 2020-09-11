# CodePipeline for webiny.com CMS
This AWS CDK project will create a CodePipeline to deploy the webiny.com cms. The aim is to allow a team to work on the same project using the same state files. All environment and state files are stored in s3 buckets and will be used by CodeBuild to read / write new states.


## Deploy the pipeline

* clone this repo
* create a new virtual environment: `python3 -m venv .env && source .env/bin/activate`
* install dependencies: `pip3 install -r requirements.txt`
* synth the project to check if everything is okay: `cdk synth '*' -c project='projectname'`
* deploy the stack: `cdk deploy '*' -c project='projectname'` (the context 'project' is needed!)

## Deploy webiny
This setup is specifically for the headless only installation of webiny. For the full installation the `apps/site/.env.json` file has to be added to the s3 bucket and to the buildspecs.
### Prepare the environment files
* create a new webiny project
* setup the `.env.json` in the project root and upload it to `projectname-environment-bucket-prod` with the name `root.env.json`  
`aws s3 cp .env.json "s3://projectname-environment-bucket-prod/root.env.json"`
* setup the `api/.env.json` and upload it to `projectname-environment-bucket-prod` with the name `api.env.json`  
`aws s3 cp api/.env.json "s3://projectname-environment-bucket-prod/api.env.json"`
* setup the `.apps/admin/.env.json` and upload it to `projectname-environment-bucket-prod` with the name `admin.env.json`  
`aws s3 cp apps/admin/.env.json "s3://projectname-environment-bucket-prod/admin.env.json"`

### Create the buildspec files
In the root of your new webiny project create the following two files (replace the projectname):  
* buildspec-api.yml:
```
version: 0.2 
phases: 
  install:
     runtime-versions:
      nodejs: 12
     commands:
      - echo "Download webiny state files from s3 bucket..."
      - aws s3 cp s3://projectname-state-bucket-$ENVIRONMENT/ .webiny --recursive
      - echo "Download webiny environment files from s3 bucket..."
      - aws s3 cp "s3://projectname-environment-bucket-$ENVIRONMENT/admin.env.json" apps/admin/.env.json
      - aws s3 cp "s3://projectname-environment-bucket-$ENVIRONMENT/api.env.json" api/.env.json 
      - aws s3 cp "s3://projectname-environment-bucket-$ENVIRONMENT/root.env.json" .env.json
      - yarn
  build:
    commands:
      - yarn webiny deploy api --env=$ENVIRONMENT
  post_build:
    commands:
      - echo "Upload webiny environment files to s3 bucket..."
      - aws s3 cp apps/admin/.env.json "s3://projectname-environment-bucket-$ENVIRONMENT/admin.env.json"
      - aws s3 cp api/.env.json "s3://projectname-environment-bucket-$ENVIRONMENT/api.env.json"
      - aws s3 cp .env.json "s3://projectname-environment-bucket-$ENVIRONMENT/root.env.json"
      - echo "Upload webiny state files to s3 bucket..."
      - aws s3 cp .webiny s3://projectname-state-bucket-$ENVIRONMENT/ --recursive
artifacts:
  type: zip
  files:
    - "**/*"
```
* buildspec-apps.yml:
```
version: 0.2 
phases: 
  install:
     runtime-versions:
      nodejs: 12
     commands:
      - echo "Download webiny state files from s3 bucket..."
      - aws s3 cp s3://projectname-state-bucket-$ENVIRONMENT/ .webiny --recursive
      - echo "Download webiny environment files from s3 bucket..."
      - aws s3 cp "s3://projectname-environment-bucket-$ENVIRONMENT/admin.env.json" apps/admin/.env.json
      - aws s3 cp "s3://projectname-environment-bucket-$ENVIRONMENT/api.env.json" api/.env.json 
      - aws s3 cp "s3://projectname-environment-bucket-$ENVIRONMENT/root.env.json" .env.json
      - yarn
  build:
    commands:
      - yarn webiny deploy apps --env=$ENVIRONMENT
  post_build:
    commands:
      - echo "Upload webiny environment files to s3 bucket..."
      - aws s3 cp apps/admin/.env.json "s3://projectname-environment-bucket-$ENVIRONMENT/admin.env.json"
      - aws s3 cp api/.env.json "s3://projectname-environment-bucket-$ENVIRONMENT/api.env.json"
      - aws s3 cp .env.json "s3://projectname-environment-bucket-$ENVIRONMENT/root.env.json"
      - echo "Upload webiny state files to s3 bucket..."
      - aws s3 cp .webiny s3://projectname-state-bucket-$ENVIRONMENT/ --recursive
artifacts:
  type: zip
  files:
    - "**/*"
```

### Push to your CodeCommit repo
set the origin of your local webiny repository to the CodeCommit repository that was created during the stack deployment.
Check the status of your deployment in the CodePipeline web console.
