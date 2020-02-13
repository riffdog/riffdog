"""
This module is for EC2 instance processing - terraform & boto and comparison.
"""

import logging
from ..data_structures import ReportElement
from ..resource import AWSResource, register

logger = logging.getLogger(__name__)

@register("aws_s3_bucket")
class S3Buckets(AWSResource):
    _states_found = {}
    _real_buckets = {}


    def fetch_real_resources(self, region):
        logging.info("Looking for s3 resources")

        client = self._get_client('s3', region)

        response = client.list_buckets()

        for bucket in response['Buckets']:
            self._real_buckets[bucket['Name']] = bucket

        
    def process_state_resource(self, state_resource, state_filename):
        
        self._states_found[state_resource['name']] = state_resource


    def compare(self, config, depth):
        # this function should be called once, take the local data and return
        # an array of result elements.
        out_report = ReportElement()

        for key, val in self._states_found.items():
            if key not in self._real_buckets:
                out_report.in_tf_but_not_aws.append(key)
            else:
                out_report.matched.append(key)

        for key, val in self._real_buckets.items():
            if key not in self._states_found:
                out_report.in_aws_but_not_tf.append(key)

        print()
        return out_report

