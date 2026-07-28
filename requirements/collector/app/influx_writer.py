import os
import logging
from typing import Dict, Any, List, Union
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfluxDBWriter:
    """
    A generic module to send collected metrics to InfluxDB.
    """
    def __init__(self):
        self.host = os.getenv("INFLUXDB_HOST", "influxdb3")
        self.port = os.getenv("INFLUXDB_HTTP_PORT", "8181")
        self.url = f"http://{self.host}:{self.port}"

        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG", "local_org")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "local_system")

        if not self.token:
            logger.warning("INFLUXDB_TOKEN is not set. Writes may fail if authentication is required.")

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def create_write_point(self, measurement: str, tags: Dict[str, str], fields: Dict[str, Any], timestamp=None):
        """
        Writes a single measurement to InfluxDB.

        :param measurement: Name of the measurement (e.g., 'system_metrics', 'hypervisor_metrics')
        :param tags: Dictionary of tag keys and values
        :param fields: Dictionary of field keys and values
        :param timestamp: Optional timestamp for the point
        """
        try:
            point = Point(measurement)

            for key, value in tags.items():
                point = point.tag(key, value)

            for key, value in fields.items():
                point = point.field(key, value)

            if timestamp:
                point = point.time(timestamp)

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logger.debug(f"Data written successfully for measurement: {measurement}")

        except Exception as e:
            logger.error(f"Failed to write point to InfluxDB: {e}")

    def write_point(self, point:Point):
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logger.debug(f"Data written successfully")
        except Exception as e:
            logger.error(f"Failed to write point to InfluxDB: {e}")


    def write_records(self, records: Union[List[Point], List[Dict], Point, Dict]):
        """
        Writes one or multiple records to InfluxDB.

        :param records: A single record or a list of records. Records can be Point objects or dictionaries.
        """
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=records)
            logger.debug("Records written successfully.")
        except Exception as e:
            logger.error(f"Failed to write records to InfluxDB: {e}")

    def write_line(self, line: str):
        """
        Writes a line protocol string to InfluxDB.

        :param line: The line protocol string to write.
        """
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=line)
            logger.debug("Line written successfully.")
        except Exception as e:
            logger.error(f"Failed to write line to InfluxDB: {e}")

    def close(self):
        """
        Close the client connection.
        """
        self.client.close()

writer = InfluxDBWriter()
