import os

from riffdog.config import RDConfig

DEFAULT_REGION="us-east-1"

def add_args(parser):

    group = parser.add_argument_group('Test Resources')
    group.add_argument('--test_value', help="append a value to test_value", action='append')
    
def config():
    config = RDConfig()
    config.test_default_value = "some default value"


