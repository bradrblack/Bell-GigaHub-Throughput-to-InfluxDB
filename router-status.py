#
# This python script uses the sagemcom API to grab bytes sent and received from the Fiber and 10Gbase-T port on a Bell GigaHub 2.0 and send the data to InfluxDB
# 
# Based on: https://github.com/iMicknl/python-sagemcom-api 
#
# The thing that took the longest to figure out is that the XPath for Interface[SFP] is actually Device/Ethernet/Interfaces/Interface[5]
#

import asyncio
import json
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod
from sagemcom_api.exceptions import  *
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import os

# --- Configuration ---
# It is recommended to use environment variables for sensitive data
url = "<your-influx-db-URL>:8086"         # e.g., "http://localhost:8086" or you
r Cloud URL
token = "<your-token>"          # e.g., "qWpu90WO..."
org = "<your-org>"             # e.g., "my_organization"
bucket = "<your-bucket>"       # e.g., "my_bucket"

# --- Instantiate the Client ---
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

HOST = "<router-IP>
USERNAME = "admin"
PASSWORD = "<your-router-password>"
ENCRYPTION_METHOD = EncryptionMethod.SHA512 # or EncryptionMethod.MD5
VALIDATE_SSL_CERT = True

async def main() -> None:
    async with SagemcomClient(HOST, USERNAME, PASSWORD, ENCRYPTION_METHOD, verif
y_ssl=VALIDATE_SSL_CERT) as client:
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

#        # Retrieve values via XPath notation, output is a dict
        try:
            summary = await client.get_value_by_xpath("Device/Optical/Interfaces")
        except UnknownPathException as exception:
            print("The xpath does not exist.")

        bytes_sent = summary[0]['stats']['bytes_sent']
        bytes_received = summary[0]['stats']['bytes_received']

#        # Retrieve values via XPath notation, output is a dict
        try:
            summary = await client.get_value_by_xpath("Device/Ethernet/Interfaces/Interface[5]")
        except UnknownPathException as exception:
            print("The xpath does not exist.")

        bytes_sent_10g = summary['interface']['stats']['bytes_sent']
        bytes_received_10g = summary['interface']['stats']['bytes_received']

        r = influxdb_client.Point("bytes_received").field("value", bytes_received)
# --- Write the Data Point ---
    try:
        write_api.write(bucket=bucket, org=org, record=r)
    except Exception as e:
        print(f"An error occurred: {e}")

    s = influxdb_client.Point("bytes_sent").field("value", bytes_sent)
    try:
        write_api.write(bucket=bucket, org=org, record=s)
    except Exception as e:
        print(f"An error occurred: {e}")

    r_10g = influxdb_client.Point("bytes_received_10g").field("value", bytes_received_10g)
# --- Write the Data Point ---
    try:
        write_api.write(bucket=bucket, org=org, record=r_10g)
    except Exception as e:
        print(f"An error occurred: {e}")

    s_10g = influxdb_client.Point("bytes_sent_10g").field("value", bytes_sent_10g)
    try:
        write_api.write(bucket=bucket, org=org, record=s_10g)
    except Exception as e:
        print(f"An error occurred: {e}")

asyncio.run(main())
