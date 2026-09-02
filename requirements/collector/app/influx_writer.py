import logging
import os
from typing import Dict, List, Union

import requests
from influxdb_client_3 import Point, InfluxDBClient3, write_client_options, WriteOptions, InfluxDBError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def success(self, data: str):
    print(f"Success writing batch: {data}")

def error(self, data: str, err: InfluxDBError):
    print(f"Error writing batch: {err}")

def retry(self, data: str, err: InfluxDBError):
    print(f"Retry error writing batch: {err}")

class InfluxDBWriter:
    """
    A generic module to send collected metrics to InfluxDB.
    """
    def __init__(self):
        self.token = os.environ.get("INFLUXDB_TOKEN", "")
        self.database = os.environ.get("INFLUXDB_BUCKET", "local_system")
        self.host = os.environ.get("INFLUXDB_HOST", "influxdb3")
        self.port = int(os.environ.get("INFLUXDB_PORT", "8181"))
        self.base_url = f"http://{self.host}:{self.port}"

        if not self.token:
            logger.warning("INFLUXDB_TOKEN is not set. Writes may fail if authentication is required.")

        self._create_database_if_not_exists()
        self.write_options = WriteOptions(batch_size=500,
                             flush_interval=10_000,
                             jitter_interval=2_000,
                             retry_interval=5_000,
                             max_retries=5,
                             max_retry_delay=30_000,
                             exponential_base=2)
        self.wco = write_client_options(success_callback=success,
                                   error_callback=error,
                                   retry_callback=retry,
                                   write_options=self.write_options)
        self.client = InfluxDBClient3(host=self.base_url,
                                      database=self.database,
                                      token=self.token,
                                      write_client_options=self.wco)

    def _create_database_if_not_exists(self):
        url = f"{self.base_url}/api/v3/configure/database"
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
