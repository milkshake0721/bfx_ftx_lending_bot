from ftxclient import FtxClient
import api_data

FTX_API_KEY = api_data.ftx["apiKey"]
FTX_API_SECRET = api_data.ftx["secret"]
FTX_API_SUBACCOUNT = api_data.ftx["subaccount"]

ftx = FtxClient(
    api_key=FTX_API_KEY, api_secret=FTX_API_SECRET, subaccount_name=FTX_API_SUBACCOUNT
)

for i in ftx.get_saved_addresses():
    print(i)
