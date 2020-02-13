"""
This module is for RDS Clusters
"""

import logging

from riffdog.data_structures import ReportElement
from riffdog.resource import AWSResource, register

logger = logging.getLogger(__name__)


@register("aws_rds_cluster")
class AWSRDSCluster(AWSResource):
    _clusters_in_aws = {}
    _clusters_in_state = {}

    def fetch_real_regional_resources(self, region):
        logging.info("Looking for RDS resources")

        client = self._get_client("rds", region)

        response = client.describe_db_clusters()

        for cluster in response["DBClusters"]:
            self._clusters_in_aws[cluster["DBClusterIdentifier"]] = cluster

    def process_state_resource(self, state_resource, state_filename):
        for instance in state_resource["instances"]:
            self._clusters_in_state[instance["attributes"]["cluster_identifier"]] = instance

    def compare(self, config, depth):
        out_report = ReportElement()

        for key, val in self._clusters_in_state.items():
            if key not in self._clusters_in_aws:
                out_report.in_tf_but_not_real.append(key)
            else:
                out_report.matched.append(key)

        for key, val in self._clusters_in_aws.items():
            if key not in self._clusters_in_state:
                out_report.in_real_but_not_tf.append(key)

        return out_report


@register("aws_rds_cluster_instance")
class AWSRDSClusterInstance(AWSResource):
    """
    These are a faux thing to Terraform. An aws_rds_cluster_instance is
    just an aws_db_instance that belongs to a Cluster.
    """
    _instances_in_aws = {}
    _instances_in_state = {}

    def fetch_real_regional_resources(self, region):
        logging.info("Looking for RDS resources")

        client = self._get_client("rds", region)

        response = client.describe_db_instances()

        for instance in response["DBInstances"]:
            if "DBClusterIdentifier" in instance:
                if instance["DBClusterIdentifier"]:
                    self._instances_in_aws[instance["DBInstanceIdentifier"]] = instance

    def process_state_resource(self, state_resource, state_filename):
        for instance in state_resource["instances"]:
            self._instances_in_state[instance["attributes"]["identifier"]] = instance

    def compare(self, config, depth):
        out_report = ReportElement()

        for key, val in self._instances_in_state.items():
            if key not in self._instances_in_aws:
                out_report.in_tf_but_not_real.append(key)
            else:
                out_report.matched.append(key)

        for key, val in self._instances_in_aws.items():
            if key not in self._instances_in_state:
                out_report.in_real_but_not_tf.append(key)

        return out_report
