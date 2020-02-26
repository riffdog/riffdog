import functools
import logging

import boto3

from .config import RDConfig

logger = logging.getLogger(__name__)


class ResourceDirectory(object):
    """
    This is the primary storage of resource mapping.
    """
    # This is the resource directory singleton. There can be only one.

    class __ResourceDirectory:
        found_resources = {}    # this is a dictionary of class instantiators
        resource_aliases = {}   # this is a dictionary aliases to above

        resource_instances = {} # this is a dictionary of actual instances

        _items = [] # this is the array of items

        _terraform_items = {}
        _real_items = {}

        def __init__(self):
            self.found_resources = {}

        def __str__(self):
            return str(self.found_resources) # FIXME - confirm both __init__ and __str__ 

        def add_item(self, item):
            if not item in self._items:
               self._items.append(item)
            self.update_indexes(item)

        def update_item_indexes(self, item):
            # add indexes!
            if item.in_real_world:
                self._real_items[item.real_id] = item
            
            if item.in_terraform:
                self._terraform_items[item.real_id] = item

        def get_item(self, terraform_id=None, real_id=None):
            
            # WARNING: multiple return paths

            if not terraform_id and not real_id:
                raise ArgumentException("Must have one of terraform_id or real_id")

            elif terraform_id:
                if not terraform_id in self._terraform_items:
                    raise KeyError("id %s not in known terraform items" % terraform_id)
                else:
                    return self._terraform_items[terraform_id]
            
            elif real_id:
                if not real_id in self._real_items:
                    raise KeyError("is %s not in known real items" % real_id)
                else:
                    return self._real_items[real_id]

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
    Base Resource Class - resources should inherit this and implement *all* of the
    functions in it - or they should implemented with a middle-layer that handles
    things like access control for the 'real' component of the resource.

    If a module does not implement one of these functions, then the scanner may halt
    execution.

    Order of execution of the framework is:

    * Scan step - the scanner will scan the state, and each state that matches either the primary, or aliased key will then call :py:func:`process_state_resource`. The order of module execution here is related to the order they are in the state files, and the order of state files that were scanned (i.e. alphabetically inside the folder, and in order that the state_folders was given in the scan config).
    * Gather 'real' items step. The scanner will then call :py:func:`fetch_real_resources` once. If the module has filled out any :py:data:`depends_on`, then it will call :py:func:`fetch_real_resources` on those modules *before* calling this function. This allows developers to pull related 'child' objects before trying to pull parents, improving optimisation and stopping duplicate pull requests.
    * Once all 'real' fetches have finished, then the scanner will call :py:func:`compare` on each module once. Again, if :py:data:`depends_on` has any values, then these modules are called prior to this instance.

    """

    depends_on = [] 
    """
    This is an array of object references used to control the fetch_real_resources
    and compare functions. 
    
    i.e. depends_on = [Foo] where Foo is a class reference.
    """

    def fetch_real_resources(self):
        """
        This may be called multiple times for each region in the scan list
        i.e. append
        """
        raise NotImplementedError()

    def process_state_resource(self, state_resource):
        """
        This function is called potentially multiple times as each resource
        is discovered by the state scanner i.e. append results to local storage.
        """
        raise NotImplementedError()

    def compare(self, depth):
        """
        this function should be called once, take the local data and return
        an array of :py:class:`ReportElement`.
        """
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
