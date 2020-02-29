"""
This module exists to hold data structures common across modules, the scanner
and the command line interface
"""

from .resource import ResourceDirectory


# class ReportElement:
#     """
#     Output report object for reporting things it finds.
#     """

#     matched = None
#     """
#     An array of items that were present in both Terraform and Real
#     """

#     in_tf_but_not_real = None
#     """
#     An array of items that Terraform thought should be there, but could not be found
#     """

#     in_real_but_not_tf = None
#     """
#     An array of items that are there, but were not in the Terraform state files
#     """

#     def __init__(self):
#         self.matched = []
#         self.in_tf_but_not_real = []
#         self.in_real_but_not_tf = []


class FoundItem:
    """
    An item that has been found, either in the state files *or* in the real world.
    """

    _terraform_id = None
    _real_id = None
    _predicted_id = None

    item_type = None
    """
    The resource type of the item found (terraform naming strategy)
    """

    dirty = False
    """
    Whether this item is or isn't the same as the terraform state thinks (only valid)
    if matched.
    """

    @property
    def terraform_id(self):
        """
        The id in terraform i.e. how Terraform refers to it - set if found in a state
        Setting this updates the index dictionary.
        """
        return self._terraform_id

    @terraform_id.setter
    def terraform_id(self, value):
        self._terraform_id = value
        rd = ResourceDirectory()
        rd.update_item_indexes(self)

    @property
    def real_id(self):
        """
        The ID that the 'real world' refers to it i.e. set if found in real world, 
        e.g. an aws ARN, instance id or s3 bucket name, or a cloudflare record id.
        Setting this updates the index dictionary.
        """
        return self._real_id

    @real_id.setter
    def real_id(self, value):
        self._real_id = value
        rd = ResourceDirectory()
        rd.update_item_indexes(self)

    @property
    def predicted_id(self):
        """
        What is the predicted ID in the real world (as Terraform thinks). May 
        return None
        """
        return self._predicted_id

    @predicted_id.setter
    def predicted_id(self, value):
        self._predicted_id = value
        rd = ResourceDirectory()
        rd.update_item_indexes(self)


    state_data = None
    """
    If there terraform id is set, this should be used to store the state data
    """

    real_data = None
    """
    This should be used to store the real data (if any). This might be used
    by comparison levels.
    """

    @property
    def matched(self):
        """
        Whether this item is both in terraform and real world.
        """
        if self._terraform_id and self._real_id:
            return True
        else:
            return False


    @property
    def in_real_world(self):
        """
        Whether this item has been detected in the real world. Use this over other
        methodds.
        """
        if self._real_id:
            return True
        else:
            return False

    @property
    def in_terraform(self):
        """
        Whether this item has been detected in the terraform state or not. Use
        this over other inspections for future compatibility.
        """
        if self._terraform_id:
            return True
        else:
            return False
    

    def __init__(self, item_type, terraform_id=None, real_id=None, state_data=None, real_data=None, predicted_id=None):

        self.item_type = item_type

        self._terraform_id = terraform_id
        self._real_id = real_id
        self._predicted_id = predicted_id
        self.state_data = state_data
        self.real_data = real_data
        self.dirty = False

        rd = ResourceDirectory()
        rd.add_item(self)


    def __str__(self):
        output = ""

        if self.matched:
            return "Matched item TF: [%s] <-> Real [%s]" % (self.terraform_id, self.real_id)
        elif self.in_terraform:
            return "Terraform item id [%s]" % self.terraform_id
        elif self.in_real_world:
            return "Real Object id [%s]" % self.real_id
        
        raise Exception("This is an invalid object not in Terraform OR Real")
