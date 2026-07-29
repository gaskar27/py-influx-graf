import os
import logging
from typing import Dict, List, Union
from influxdb_client_3 import Point, InfluxDBClient3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfluxDBWriter:
    """
    A generic module to send collected metrics to InfluxDB.
    """
    def __init__(self):
        self.host = os.environ.get("INFLUXDB_HOST", "localhost")
        self.port = os.environ.get("INFLUXDB_HTTP_PORT", "8181")
        self.url = f"http://{self.host}:{self.port}"

        self.token = os.getenv("INFLUXDB_TOKEN")
        self.database = os.environ.get("INFLUXDB_BUCKET", "local_system")

        if not self.token:
            logger.warning("INFLUXDB_TOKEN is not set. Writes may fail if authentication is required.")

        self.client = InfluxDBClient3(url=self.url, database=self.database, token=str(self.token))

    def write_point(self, point:Point):
        try:
            self.client.write(point)
            logger.debug(f"Data written successfully")
        except Exception as e:
            logger.error(f"Failed to write point to InfluxDB: {e}")

    def write_records(self, records: Union[List[Point], List[Dict], Point, Dict]):
        """
        Writes one or multiple records to InfluxDB.

        :param records: A single record or a list of records. Records can be Point objects or dictionaries.
        """
        try:
            self.client.write(record=records, write_precision="ms")
            logger.debug("Records written successfully.")
        except Exception as e:
            logger.error(f"Failed to write records to InfluxDB: {e}")

    def write_line(self, line: str):
        """
        Writes a line protocol string to InfluxDB.

        :param line: The line protocol string to write.
        """
        try:
            self.client.write(record=line, write_precision="ms")
            logger.debug("Line written successfully.")
        except Exception as e:
            logger.error(f"Failed to write line to InfluxDB: {e}")

    def close(self):
        """
        Close the client connection.
        """
        self.client.close()

writer = InfluxDBWriter()
