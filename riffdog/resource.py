import functools
import logging

import boto3

from .data_structures import RDConfig

logger = logging.getLogger(__name__)


class ResourceDirectory(object):
    # This is the resource directory singleton. There can be only one.

    class __ResourceDirectory:
        found_resources = {}    # this is a dictionary of class instantiators
        resource_aliases = {}   # this is a dictionary aliases to above

        resource_instances = {} # this is a dictionary of actual instances

        def __init__(self):
            self.found_resources = {}

        def __str__(self):
            return str(self.found_resources)

        def add(self, key, target_type):
            self.found_resources[key] = target_type

        def lookup(self, key):

            # Warning: multiple return paths in this function

            if key in self.resource_instances:
                return self.resource_instances[key]
            else:
                if key in self.resource_aliases and self.resource_aliases[key] in self.resource_instances:
                    return self.resource_instances[self.resource_aliases[key]]
            
            # if got this far, its not an instance, so try to make one

            if key in self.found_resources:
                instance = self.found_resources[key]()
                self.resource_instances[key] = instance
                return instance
            elif key in self.resource_aliases:
                instance = self.found_resources[self.resource_aliases[key]]()
                self.resource_instances[key] = instance
                return instance
            else:
                # Not in the mapping or as an alias :. not scanned
                return None

        def add_alias(self, key, alias):
            self.resource_aliases[alias] = key

    instance = None

    def __new__(cls):  # __new__ always a classmethod
        if not ResourceDirectory.instance:
            ResourceDirectory.instance = ResourceDirectory.__ResourceDirectory()
        return ResourceDirectory.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)


def register(*args):

    def actual_decorator(constructor):
        resource_name, *aliases = args
        logger.info("Resource tagged {name} ({aliases}) - {constructor}".format(
            name=resource_name,
            aliases=", ".join(a for a in aliases),
            constructor=constructor))

        @functools.wraps(constructor)
        def wrapper(*args, **kwargs):
            return constructor(*args, **kwargs)

        rd = ResourceDirectory()

        rd.add(resource_name, wrapper)
        if aliases:
            for alias in aliases:
                rd.add_alias(resource_name, alias)

        RDConfig().base_elements_to_scan.append(resource_name)

        return wrapper
    return actual_decorator


class Resource:
    """
    Base Resource Class
    """

    depends_on = []

    def fetch_real_resources(self):
        # This may be called multiple times for each region in the scan list
        # i.e. append
        raise NotImplementedError()

    def process_state_resource(self, state_resource):
        # This function is called potentially multiple times as each resource
        # is discovered by the state scanner i.e. append results to local store
        raise NotImplementedError()

    def compare(self, depth):
        # this function should be called once, take the local data and return
        # an array of result elements.
        raise NotImplementedError()


# FIXME: this might want to go into a specific module for namespacing?

class AWSResource(Resource):
    """
    Middle Inheritance to handle getting the correct client & resource objects
    """

    # set this to False if this class is a Global resource (e.g. s3)
    regional_resource = True

    def fetch_real_resources(self):
        
        if self.regional_resource:
            for region in RDConfig().regions:
                self.fetch_real_regional_resources(region)
        else:
            self.fetch_real_global_resources()

    def fetch_real_regional_resources(self, region):
        raise NotImplemented()

    
    def fetch_real_global_resources(self):
        raise NotImplemented()
    

    def _get_client(self, aws_client_type, region):

        # FIXME: Some previous code to bring back to allow alternative queries

        # if account.auth_method == Account.IAM_ROLE:
        #     credentials = _get_sts_credentials(account)
        #     client = boto3.client(
        #         aws_client_type,
        #         region_name=region, aws_access_key_id=credentials['AccessKeyId'],
        #         aws_secret_access_key=credentials['SecretAccessKey'],
        #         aws_session_token=credentials['SessionToken'])
        # else:
        #   client = boto3.client(
        #       aws_client_type,
        #       region_name=region,
        #       aws_access_key_id=account.key,
        #       aws_secret_access_key=account.secret)

        client = boto3.client(aws_client_type, region_name=region)
        return client

    def _get_resource(self, aws_resource_type, region):
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
