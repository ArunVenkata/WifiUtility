from common import API_URL
from utils import log_error
import json
import urllib.request as req
import urllib
import tablib
def get_data():

    try:
        contents = req.urlopen(API_URL).read()
        return {
            "success": True,
            "message": "Data Found",
            "data": json.loads(contents)
        }
    except Exception as e:
        return {
            "success": False,
            "message": e,
        }


response = get_data()
if not response['success']:
    log_error("Error Occurred with API")
    exit(1)
dataset = tablib.Dataset(headers=['id', 'description', 'date', "action", "user_id", "criticality"])
dataset.json = json.dumps(response['data'])
with open("excel_file.xlsx", 'wb') as file:
    file.write(dataset.export('xlsx'))
