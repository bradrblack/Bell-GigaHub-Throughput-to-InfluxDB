import asyncio
import json
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod
from sagemcom_api.exceptions import  *

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import os

# --- InfluxDB Configuration ---
# It is recommended to use environment variables for sensitive data
url = "<>"         # e.g., "http://localhost:8086" or your Cloud URL
token = "<>"          # e.g., "qWpu90WO..."
org = "<>"             # e.g., "my_organization"
bucket = "<>"       # e.g., "my_bucket"

# --- Instantiate the Client ---
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

HOST = "<router>"
USERNAME = "admin"
PASSWORD = "<pass>"
ENCRYPTION_METHOD = EncryptionMethod.SHA512 # or EncryptionMethod.MD5
VALIDATE_SSL_CERT = True

async def main() -> None:
    async with SagemcomClient(HOST, USERNAME, PASSWORD, ENCRYPTION_METHOD, verify_ssl=VALIDATE_SSL_CERT) as client:
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

        devices = await client.get_hosts()

# Initialize counters
        AirNet = 0
        Guest = 0

        for device in devices:
            if device.active:
                # Extract the AccessPoint Alias from the associated_device string
                apa = device.associated_device

                # Find the Alias
                if "AccessPoint[Alias=" in apa:
                    start = apa.find("AccessPoint[Alias='") + len("AccessPoint[Alias='")
                    end = apa.find("']", start)
                    alias_id = apa[start:end]

                    # Count devices per alias

                    if alias_id in ['PRIV2', 'VID2', 'PRIV0']:
                        AirNet += 1
                    elif alias_id in ['GUEST2', 'GUEST1']:
                        Guest += 1

        # Retrieve values via XPath notation, output is a dict
        try:
            summary = await client.get_value_by_xpath("Device/Optical/Interfaces")
        except UnknownPathException as exception:
            print("The xpath does not exist.")

        bytes_sent = summary[0]['stats']['bytes_sent']
        bytes_received = summary[0]['stats']['bytes_received']

        # Retrieve values via XPath notation, output is a dict
        try:
            summary = await client.get_value_by_xpath("Device/Ethernet/Interfaces/Interface[5]")
        except UnknownPathException as exception:
            print("The xpath does not exist.")

        bytes_sent_10g = summary['interface']['stats']['bytes_sent']
        bytes_received_10g = summary['interface']['stats']['bytes_received']


        # Retrieve values via XPath notation, output is a dict
        try:
            summary = await client.get_value_by_xpath("Device/WiFi/SSIDs")

        except UnknownPathException as exception:
            print("The xpath does not exist.")

# Find interface by alias
        for interface in summary:
            if interface['alias'] == 'WL_PRIV':
                bytes_received_Priv_24 = int(interface['stats']['bytes_received'])
                bytes_sent_Priv_24 = int(interface['stats']['bytes_sent'])
            elif interface['alias'] == 'WL_GUEST':
                bytes_received_Guest_24 = int(interface['stats']['bytes_received'])
                bytes_sent_Guest_24 = int(interface['stats']['bytes_sent'])
            elif interface['alias'] == 'WL_GUEST_5G':
                bytes_received_Guest_5 = int(interface['stats']['bytes_received'])
                bytes_sent_Guest_5 = int(interface['stats']['bytes_sent'])
            elif interface['alias'] == 'WL_GUEST_6G':
                bytes_received_Guest_6 = int(interface['stats']['bytes_received'])
                bytes_sent_Guest_6 = int(interface['stats']['bytes_sent'])
            elif interface['alias'] == 'WL_DATA_5G':
                bytes_received_Priv_5 = int(interface['stats']['bytes_received'])
                bytes_sent_Priv_5 = int(interface['stats']['bytes_sent'])
            elif interface['alias'] == 'WL_PRIV_6G':
                bytes_received_Priv_6 = int(interface['stats']['bytes_received'])
                bytes_sent_Priv_6 = int(interface['stats']['bytes_sent'])

# Define your data points with meaningful names
    data_points = [
    ("bytes_sent_priv_24", bytes_sent_Priv_24),
    ("bytes_received_priv_24", bytes_received_Priv_24),
    ("bytes_sent_priv_5", bytes_sent_Priv_5),
    ("bytes_received_priv_5", bytes_received_Priv_5),
    ("bytes_sent_priv_6", bytes_sent_Priv_6),
    ("bytes_received_priv_6", bytes_received_Priv_6),
    ("bytes_sent_guest_24", bytes_sent_Guest_24),
    ("bytes_received_guest_24", bytes_received_Guest_24),
    ("bytes_sent_guest_5", bytes_sent_Guest_5),
    ("bytes_received_guest_5", bytes_received_Guest_5),
    ("bytes_sent_guest_6", bytes_sent_Guest_6),
    ("bytes_received_guest_6", bytes_received_Guest_6),
 ]

# Write each data point to InfluxDB
    for measurement_name, value in data_points:
        point = influxdb_client.Point(measurement_name).field("value", value)
        try:
            write_api.write(bucket=bucket, org=org, record=point)
        except Exception as e:
            print(f"Error writing {measurement_name}: {e}")

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

    AirNet_p = influxdb_client.Point("AirNet_Count").field("value", AirNet)
    try:
        write_api.write(bucket=bucket, org=org, record=AirNet_p)
    except Exception as e:
        print(f"An error occurred: {e}")

    Guest_p = influxdb_client.Point("Guest_Count").field("value", Guest)
    try:
        write_api.write(bucket=bucket, org=org, record=Guest_p)
    except Exception as e:
        print(f"An error occurred: {e}")


asyncio.run(main())
