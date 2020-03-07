from riffdog.data_structures import FoundItem
from riffdog.resource import register, ResourceDirectory, Resource

@register("test_item_one")
class TestItemOne(Resource):

    def fetch_real_resources(self):
        rd = ResourceDirectory()

        items = ["Number One (4-1)", "Not In TF"]
        
        for entry in items:
            try:
                item = rd.get_item(predicted_id=entry)
                item.real_id = entry
                item.real_data = entry
            except KeyError:
                FoundItem(self.resource_type, real_id=entry, real_data=entry)
       
    def process_state_resource(self, state_resource, state_filename):
        for instance in state_resource['instances']:
            FoundItem(self.resource_type, terraform_id=instance["attributes"]["id"], predicted_id=instance["attributes"]["id"], state_data=instance)
    
    def compare(self, item, depth):
        pass

@register("test_item_three", "test_item_four")
class TestItemThree(Resource):

    def fetch_real_resources(self):
        pass
        #item = FoundItem(self.resource_type, real_id=instance["DBInstanceIdentifier"], real_data=instance)

    def process_state_resource(self, state_resource, state_filename):
        for instance in state_resource['instances']:
            item = FoundItem(self.resource_type, terraform_id=instance["attributes"]["id"], state_data=instance)
    
    def compare(self, item, depth):
        pass
