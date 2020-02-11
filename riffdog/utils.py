
import boto3

def _get_client(aws_client_type, region):

    # FIXME: Some previous code to bring back to allow alternative queries

    # if account.auth_method == Account.IAM_ROLE:
    #     credentials = _get_sts_credentials(account)
    #     client = boto3.client(
    #         aws_client_type,
    #         region_name=region, aws_access_key_id=credentials['AccessKeyId'],
    #         aws_secret_access_key=credentials['SecretAccessKey'],
    #         aws_session_token=credentials['SessionToken'])
    #else:
    #   client = boto3.client(
    ##        aws_client_type,
     #       region_name=region,
     #       aws_access_key_id=account.key,
     #       aws_secret_access_key=account.secret)

    client = boto3.client(aws_client_type, region_name=region)
    
    return client

def _get_resource(aws_resource_type, region):
    # if not account:
    #     account = Account.objects.get(default=True)

    # if account.auth_method == Account.IAM_ROLE:
    #     credentials = _get_sts_credentials(account)
    #     resource = boto3.resource(
    #         aws_resource_type,
    #         region_name=region, aws_access_key_id=credentials['AccessKeyId'],
    #         aws_secret_access_key=credentials['SecretAccessKey'],
    #         aws_session_token=credentials['SessionToken'])

    # else:
    #     resource = boto3.resource(
    #         aws_resource_type,
    #         region_name=region,
    #         aws_access_key_id=account.key,
    #         aws_secret_access_key=account.secret)

    resource = boto3.resource(aws_resource_type, region_name=region)

    return resource
