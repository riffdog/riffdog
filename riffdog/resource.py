import functools
import logging

logger = logging.getLogger(__name__)




class ResourceDirectory(object):
    # This is the resource directory singleton. There can be only one.

    class __ResourceDirectory:
        found_resources = {}

        def __init__(self):
            self.found_resources = {}

        def __str__(self):
            return str(found_resources)

        def add(self, key, target_type):
            self.found_resources[key] = target_type

        def lookup(self, key):
            if key in self.found_resources:
                return self.found_resources[key]
            else:
                return None

            

    instance = None
    def __new__(cls): # __new__ always a classmethod
        if not ResourceDirectory.instance:
            ResourceDirectory.instance = ResourceDirectory.__ResourceDirectory()
        return ResourceDirectory.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)


def register(resource_name):
    
    def actual_decorator(constructor):
        logger.info("resource tagged %s - %s " % (resource_name , constructor))

        @functools.wraps(constructor)
        def wrapper(*args, **kwargs):
            return constructor(*args, **kwargs)

        rd = ResourceDirectory()
        rd.add(resource_name, wrapper)

        return wrapper
    return actual_decorator


class Resource():


    def fetch_real_resources(self, region):
        # This may be called multiple times for each region in the scan list
        # i.e. append
        raise NotImplementedError()

    def process_state_resource(state_resource):
        # This function is called potentilly multiple times as each resource
        # is discovered by the state scanner i.e. append results to local store
        raise NotImplementedError()

    def compare(self, depth):
        # this function should be called once, take the local data and return
        # an array of result elements.
        raise NotImplementedError()