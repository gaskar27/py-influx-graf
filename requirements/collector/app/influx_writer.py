import os
import logging
import requests
from typing import Dict, List, Union
from influxdb_client_3 import Point, InfluxDBClient3
from influxdb_client_3.write_client.domain import write_precision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfluxDBWriter:
    """
    A generic module to send collected metrics to InfluxDB.
    """
    def __init__(self):
        self.token = os.environ.get("INFLUXDB_TOKEN", "")
        self.database = os.environ.get("INFLUXDB_BUCKET", "local_system")

        if not self.token:
            logger.warning("INFLUXDB_TOKEN is not set. Writes may fail if authentication is required.")

        self._create_database_if_not_exists()
        self.client = InfluxDBClient3(host="influxdb3:8181", database=self.database, token=self.token)

    def _create_database_if_not_exists(self):
        url = "http://influxdb3:8181/api/v3/configure/database"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        data = {
            "db": self.database,
        }
        try:
            response = requests.post(url=url, headers=headers, json=data, timeout=5)
            if response.status_code in (200, 201):
                logger.info(f"Database '{self.database}' Created successfully.")
            elif response.status_code == 409:
                logger.info(f"Database '{self.database}' is already exists.")
            else:
                logger.debug(f"Info creation DB ({response.status_code}): {response.text}")
        except Exception as e:
            logger.warning(f"Unable to verify/create DB via API: {e}")

    def write_point(self, point:Point):
        try:
            self.client.write(record=point, write_precision="ms")
            logger.debug(f"Point written successfully")
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
