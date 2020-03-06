from riffdog.data_structures import FoundItem
from riffdog.resource import register, ResourceDirectory, Resource

@register("test_item_one")
class TestItemOne(Resource):

    def fetch_real_resources(self):
        pass
        #item = FoundItem(self.resource_type, real_id=instance["DBInstanceIdentifier"], real_data=instance)

    def process_state_resource(self, state_resource, state_filename):
        pass
    
    def compare(self, item, depth):
        pass
