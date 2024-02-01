from edu_test import *

import boto3
import time
import csv 
etl = EduTest()
etl.init()

make_res = EduResult()
list_of_buckets = []
def list_s3_buckets(access_key_id, secret_access_key, region='us-east-1'):
    s3 = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    try:
        response = s3.list_buckets()
        if 'Buckets' in response:
            buckets = response['Buckets']
            if buckets:
                for bucket in buckets:
                    
                    if bucket['Name'].startswith("my-bucket-"):
                        list_of_buckets.append(bucket['Name'])
                        make_res.add_results("bucket name check", EduResult.Pass)
                if not list_of_buckets:
                    print("No buckets starting with 'my-bucket-' found.")
                    make_res.add_results("bucket name check", EduResult.Fail)

            else:
                print("No S3 buckets found.")
                # make_res.add_results("Test1", EduResult.Fail)
        else:
            print("Failed to retrieve S3 bucket information.")

    except Exception as e:
        print(f"An error occurred while listing S3 buckets: {str(e)}")
    if len(list_of_buckets)>3:
        make_res.add_results("Quantity-of-buckets check", EduResult.Fail)
      
    else:
        try:

            # Get the bucket public access block configuration
            for bucket in list_of_buckets:
                public_access_block = s3.get_public_access_block(Bucket=bucket)
                public_Access_CheckList=[]
                public_Access_CheckList.append(public_access_block['PublicAccessBlockConfiguration']['BlockPublicAcls'])
                public_Access_CheckList.append(public_access_block['PublicAccessBlockConfiguration']['BlockPublicPolicy'])
                public_Access_CheckList.append(public_access_block['PublicAccessBlockConfiguration']['IgnorePublicAcls'])
                public_Access_CheckList.append(public_access_block['PublicAccessBlockConfiguration']['RestrictPublicBuckets'])
                
                if True in public_Access_CheckList:
                    print("TEST FAILED PUBLIC ACCESS IS NOT ALLOWED!")
                    make_res.add_results("Public access check", EduResult.Fail)
                else:
                    print("ALL CHECKS PASSED FOR CONFIGURATIONS")
                    make_res.add_results("Public access check", EduResult.Pass)
            # Check the folders of S3
            bucket_name = list_of_buckets[0]
            folders_to_check = ['AppData', 'PollyOutput', 'images']
            
            for folder in folders_to_check:
                folder_exists = s3.list_objects(Bucket=bucket_name, Prefix=folder, Delimiter='/')
                if 'CommonPrefixes' not in folder_exists:
                    print(f"Folder '{folder}' not found in bucket '{bucket_name}'.")
                    make_res.add_results(f"{folder} check", EduResult.Fail)
                else:
                    print(f"Folder '{folder}' found in bucket '{bucket_name}'.")
                    make_res.add_results(f"{folder} check", EduResult.Pass)

            
        except Exception as e:
            print(f"An error occurred while checking Block Public Access settings: {str(e)}")

def test_iam_role(access_key_id, secret_access_key, region='us-east-1'):
    role_name='RoleForMLServices'
    iam = boto3.client('iam', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    try:
        print("Inside iam role function")
        response = iam.get_role(RoleName=role_name)
        role_info = response['Role']
        print(f"IAM Role '{role_name}' found:")
        print(f"Role ARN: {role_info['Arn']}")
        print(f"Creation Time: {role_info['CreateDate']}")
        print("Role check: PASSED")
        make_res.add_results("Role-creation check", EduResult.Pass)

    except iam.exceptions.NoSuchEntityException:
        print(f"IAM Role '{role_name}' not found. Role check: FAILED")
        make_res.add_results("Role-creation check", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while checking IAM Role: {str(e)}")

    except:
        return EduResult.Fail

def check_lambda_function(access_key_id, secret_access_key, region='us-east-1'):
    lambda_function_name='LambdaForMLServices'
    expected_timeout=10
    actual_role_name='RoleForMLServices'
    runtime = 'Python 3.12'
    lambda_client = boto3.client('lambda', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    print("Inside lambda function")
    try:
        # Describe the Lambda function
        response = lambda_client.get_function(FunctionName=lambda_function_name)

        function_info = response['Configuration']
        
        print(f"Lambda function '{lambda_function_name}' found:")
        print(f"Function ARN: {function_info['FunctionArn']}")
        print(f"Last Modified: {function_info['LastModified']}")

        #Check Role attached with Lambda
        attached_role_arn = function_info['Role']
        attached_role_name = attached_role_arn.split('/')[-1]
        print("The attached role is:", attached_role_name)

        if attached_role_name == actual_role_name:
            print("Correct Role Attached")
            make_res.add_results("Lambda Role Check", EduResult.Pass)
        else:
            print("The role attached with Lambda is not RoleForMLServices")
            make_res.add_results("Lambda Role Check", EduResult.Fail)

        #Check Runtime

        actual_runtime = function_info['Runtime']
        if runtime == actual_runtime:
            print("Correct Runtime Python 3.12 selected")
            make_res.add_results("Lambda Runtime Check", EduResult.Pass)
        else:
            make_res.add_results("Python 3.12 is not selected", EduResult.Fail)

        # Check the timeout configuration
        actual_timeout = function_info['Timeout']
        print(f"Timeout configured: {actual_timeout} seconds")

        if actual_timeout == expected_timeout:
            print(f"Timeout check: PASSED")
            make_res.add_results("Lambda Timeout Check", EduResult.Pass)
        else:
            print(f"Timeout check: FAILED (Expected: {expected_timeout}, Actual: {actual_timeout})")
            make_res.add_results("Lambda Timeout Check", EduResult.Fail)

        

    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function '{lambda_function_name}' not found. Function check: FAILED")
        make_res.add_results("Lambda Function Check", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while checking Lambda Function: {str(e)}")
        make_res.add_results("Lambda Function test Check", EduResult.Fail)


def check_lambda_event_trigger(access_key_id, secret_access_key, region='us-east-1'):
    # lambda_client = boto3.client('lambda', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    # iam_client = boto3.client('iam', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    lambda_function_name='LambdaForMLServices'
    s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)

    bucket_name=list_of_buckets[0]

    try:
        response = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
        print("Response::", response)
        if 'LambdaFunctionConfigurations' in response or 'QueueConfigurations' in response or 'TopicConfigurations' in response:
            print(f"Event notifications found for S3 bucket '{bucket_name}':")
            make_res.add_results("S3 Bucket Event Notifications Check", EduResult.Pass)
            
            # Print the Lambda function configurations
            if 'LambdaFunctionConfigurations' in response:
                print("Lambda Function Configurations:")
                for config in response['LambdaFunctionConfigurations']:
                    print(f"Lambda Function ARN: {config['LambdaFunctionArn']}")
                    print(f"Events: {config['Events']}")

                    if 'Events' in config:
                        event_types = config['Events']
                        if 's3:ObjectCreated:*' in event_types:
                            print("Event type's3:ObjectCreated:*' found.")
                            make_res.add_results("Event Types Check", EduResult.Pass)
                        else: 
                            make_res.add_results("Event type is not All objects", EduResult.Fail)
                            

                    if 'Filter' in config and 'Key' in config['Filter']:
                        filter_rules = config['Filter']['Key']['FilterRules']
                        for rule in filter_rules:
                            if rule.get('Name') == 'Prefix' and rule.get('Value') == 'images/':
                                print("Filter Rule: 'images/' found.")
                                make_res.add_results("Filter Rule Check", EduResult.Pass)
                            else: 
                                make_res.add_results("Trigger not created for images/ folder Check", EduResult.Fail)

            
            # Print the queue configurations
            if 'QueueConfigurations' in response:
                print("\nQueue Configurations:")
                for config in response['QueueConfigurations']:
                    print(f"Queue ARN: {config['QueueArn']}")
                    print(f"Events: {config['Events']}")
            
            # Print the topic configurations
            if 'TopicConfigurations' in response:
                print("\nTopic Configurations:")
                for config in response['TopicConfigurations']:
                    print(f"Topic ARN: {config['TopicArn']}")
                    print(f"Events: {config['Events']}")
        else:
            print(f"No trigger created for S3 bucket")
            make_res.add_results("No trigger for S3 bucket created ", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while listing S3 bucket event notifications: {str(e)}")
        make_res.add_results("Failed to check triggers", EduResult.Fail)
       


def check_textract_output(access_key_id, secret_access_key, region='us-east-1'):
    folders = ['TextractOutput', 'RekognitionOutput']
    bucket_name = list_of_buckets[0]
    s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)

    try:
        for folder in folders:
            prefix = f"{folder}/"
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' in response:
                print(f"'{folder}' folder found in S3 bucket '{bucket_name}'.")
                make_res.add_results(f"Textract and Rekognition code executed", EduResult.Pass)
            else:
                print(f"'{folder}' folder not found in S3 bucket '{bucket_name}'.")
                make_res.add_results(f"Textract and Rekognition code not executed", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while checking S3 bucket: {str(e)}")
        make_res.add_results("Folder Check", EduResult.Fail)

def check_mp3_file_in_s3_bucket(access_key_id, secret_access_key, region='us-east-1'):
    bucket_name = list_of_buckets[0]
    print("Bucket name is:::", bucket_name)
    prefix = 'PollyOutput/'
    s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)

    try:
        # List objects in the specified S3 bucket and prefix
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        # Check if any '.mp3' file is found in the PollyOutput folder
        mp3_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.mp3')]

        if mp3_files:
            print(f".mp3 file(s) found in '{prefix}' folder of S3 bucket '{bucket_name}'.")
            make_res.add_results("MP3 File Check", EduResult.Pass)
        else:
            print(f"No .mp3 file found in '{prefix}' folder of S3 bucket '{bucket_name}'.")
            make_res.add_results("Polly task not executed", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while checking S3 bucket: {str(e)}")
        make_res.add_results("MP3 File Check", EduResult.Fail)

def lambda_function_2(access_key_id, secret_access_key, region='us-east-1'):
    lambda_function_name='LambdaForApp'
    expected_timeout=35
    actual_role_name='RoleForMLServices'
    lambda_client = boto3.client('lambda', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    print("Inside lambda function")
    try:
        # Describe the Lambda function
        response = lambda_client.get_function(FunctionName=lambda_function_name)

        function_info = response['Configuration']
        
        print(f"Lambda function '{lambda_function_name}' found:")
        print(f"Function ARN: {function_info['FunctionArn']}")
        print(f"Last Modified: {function_info['LastModified']}")

        #Check Role attached with Lambda
        attached_role_arn = function_info['Role']
        attached_role_name = attached_role_arn.split('/')[-1]
        print("The attached role is:", attached_role_name)

        if attached_role_name == actual_role_name:
            print("Correct Role Attached")
            make_res.add_results("Lambda Role Check", EduResult.Pass)
        else:
            print("The role attached with Lambda is not RoleForMLServices")
            make_res.add_results("Lambda Role Check", EduResult.Fail)

        # Check the timeout configuration
        actual_timeout = function_info['Timeout']
        print(f"Timeout configured: {actual_timeout} seconds")

        if actual_timeout == expected_timeout:
            print(f"Timeout check: PASSED")
            make_res.add_results("Lambda Timeout Check", EduResult.Pass)
        else:
            print(f"Timeout check: FAILED (Expected: {expected_timeout}, Actual: {actual_timeout})")
            make_res.add_results("Lambda Timeout Check", EduResult.Fail)
            
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function '{lambda_function_name}' not found. Function check: FAILED")
        make_res.add_results("LambdaForApp Role Check", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while checking Lambda Function: {str(e)}")
        make_res.add_results("LambdaForApp Role Check", EduResult.Fail)

def s3_bucket_cors(access_key_id, secret_access_key, region='us-east-1'):
    
    temp_bucket_name = list_of_buckets[0]
    bucket_name = str(temp_bucket_name)
    s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    
    try:
        cors_configuration= s3_client.get_bucket_cors(Bucket=bucket_name)
        make_res.add_results("CORS Policy Check", EduResult.Pass)
    except Exception as e:
        print(f"No CORS configuration found")
        make_res.add_results("CORS Policy Check", EduResult.Fail)

def check_app_output(access_key_id, secret_access_key, region='us-east-1'):
    bucket_name= list_of_buckets[0]
    s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)

    try:
        # List objects in the specified S3 bucket and prefix
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='AppOutput/')

        # Check if the folder exists
        if 'Contents' in response:
            print(f"'AppOutput' folder found in S3 bucket '{bucket_name}'.")
            make_res.add_results("AppOutput Folder Check", EduResult.Pass)
        else:
            print(f"'AppOutput' folder not found in S3 bucket '{bucket_name}'.")
            make_res.add_results("React app not executed", EduResult.Fail)

    except Exception as e:
        print(f"An error occurred while checking S3 bucket: {str(e)}")
        make_res.add_results("AppOutput Folder Check", EduResult.Fail)

if __name__ == "__main__":
    csv_file = 'credentials_IAMLabUser.csv'
    print("access:",os.getenv("access_key_id"))
    print("secret access:",os.getenv("secret_access_key"))
    print("account id:", os.getenv("account_ID"))
    try:
        list_s3_buckets(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # test_iam_role(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # check_lambda_function(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        check_lambda_event_trigger(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # check_textract_output(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # check_mp3_file_in_s3_bucket(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # lambda_function_2(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # s3_bucket_cors(os.getenv("access_key_id"), os.getenv("secret_access_key"))
        # check_app_output(os.getenv("access_key_id"), os.getenv("secret_access_key"))

    except:
        print("Can't run functions")
    
etl.post_results(make_res)
