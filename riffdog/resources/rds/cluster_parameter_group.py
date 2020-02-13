"""
This module is for RDS Cluster Parameter Groups
"""

import logging

from riffdog.data_structures import ReportElement
from riffdog.resource import AWSResource, register

logger = logging.getLogger(__name__)


@register("aws_rds_cluster_parameter_group")
class AWSRDSClusterParameterGroup(AWSResource):
    _cluster_pgs_in_aws = {}
    _cluster_pgs_in_state = {}

    def fetch_real_regional_resources(self, region):
        logging.info("Looking for RDS resources")

        client = self._get_client("rds", region)

        response = client.describe_db_cluster_parameter_groups()

        for pg in response["DBClusterParameterGroups"]:
            self._cluster_pgs_in_aws[pg["DBClusterParameterGroupName"]] = pg

    def process_state_resource(self, state_resource, state_filename):
        for instance in state_resource["instances"]:
            self._cluster_pgs_in_state[instance["attributes"]["cluster_identifier"]] = instance

    def compare(self, config, depth):
        out_report = ReportElement()

        for key, val in self._cluster_pgs_in_state.items():
            if key not in self._cluster_pgs_in_aws:
                out_report.in_tf_but_not_real.append(key)
            else:
                out_report.matched.append(key)

        for key, val in self._cluster_pgs_in_aws.items():
            if key not in self._cluster_pgs_in_state:
                out_report.in_real_but_not_tf.append(key)

        return out_report
