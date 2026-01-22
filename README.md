
This python script uses the sagemcom API to grab bytes sent and received from the Fiber port on a Bell GigaHub 2.0 and send the data to InfluxDB
 
Based on: https://github.com/iMicknl/python-sagemcom-api 

The thing that took the longest to figure out is that the XPath for Interface[SFP] is actually Device/Ethernet/Interfaces/Interface[5]
