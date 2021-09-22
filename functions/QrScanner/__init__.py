from pyzbar.pyzbar import decode
import logging
import azure.functions as func
import cv2
import json
import traceback
from shared_code.config_reader import ConfigurationFile as Configuration 
import os

from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        return run(req)
    except Exception:
        return func.HttpResponse(traceback.format_exc())

def run(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    json_data = json.dumps(req.get_json())
    values = json.loads(json_data)['values']
    video_file_path = values[0]["data"]["video_file_path"]
    record_id = values[0]["recordId"]

    results = {}
    results["values"] = []

    print(video_file_path)

    config = ConfigurationFile.get_json_file_from_url(os.path.dirname(video_file_path))

    try:
        detected_barcodes = list()
        if(config.isSectionEnabled("barcodes")):
            detected_barcodes = detect_barcodes(video_file_path)
        if len(detected_barcodes) == 0:
            val = {
                "recordId": record_id,
                "data": {
                    "barcodes":[]
                },
                "errors": None,
                "warnings": [{"message": f"No barcode is detected in video: {video_file_path}"}]
            }
            results["values"].append(val)

        else: 
            for element in detected_barcodes:
                del element["compare_timestamps"]
                element["text"] = element["barcode"]

            record = {
                    "recordId": record_id,
                    "data": {
                        "barcodes": detected_barcodes
                    },
                    "errors": None,
                    "warnings": None
                    }
            results["values"].append(record)

    except Exception as ex:
        val = {
                "recordId": None,
                "data": {
                    "barcodes":None
                },
                "errors": [{"message": ex.args}],
                "warnings": [{"message": f"The request failed to process. {traceback.format_exc()}"}]
            }
        results["values"].append(val)

    finally:    
        return func.HttpResponse(json.dumps(results,ensure_ascii=False), mimetype="application/json")

def detect_barcodes(video_file_path):
    detected_barcodes = list()
    cap = cv2.VideoCapture(video_file_path)
    i=0 #frame counter
    while(cap.isOpened()):
        ret = cap.grab()
        i=i+1 #increment counter
        if i % 10 == 0: # display only one tenth of the frames, you can change this parameter according to your needs
            if (ret != True):
                break
            ret, frame = cap.retrieve() #decode frame
            for barcode in decode(frame):
                myData = barcode.data.decode('utf-8')
                milliseconds = cap.get(cv2.CAP_PROP_POS_MSEC)
                seconds = milliseconds//1000
                milliseconds = milliseconds%1000
                minutes = 0
                hours = 0
                if seconds >= 60:
                    minutes = seconds//60
                    seconds = seconds % 60
                if minutes >= 60:
                    hours = minutes//60
                    minutes = minutes % 60
                
                startTimeStamp = f'{int(hours)}:{"%02d" % (int(minutes),)}:{"%02d" % (int(seconds),)}'
                if any(value["barcode"]==myData for value in detected_barcodes):
                    for value in detected_barcodes:

                        #logic for not taking consecutive timestamps
                        timestamp1 = datetime.strptime(value["compare_timestamps"][len(value["compare_timestamps"]) -1], "%H:%M:%S")
                        timestamp2 = datetime.strptime(startTimeStamp, "%H:%M:%S")

                        # get diffrence between startTimestamp and last value of compare_timestamps
                        difference = timestamp2 - timestamp1

                        #logic for not taking same value 
                        current_timestamp = len(value["timestamps"]) - 1
                        last_timestamp =  value["timestamps"][current_timestamp]['start']

                        if(value["barcode"]==myData and last_timestamp != startTimeStamp and startTimeStamp != '0:00:00' and difference.seconds != 0):
                            if difference.seconds > 1: value["timestamps"].append({"start": startTimeStamp, "end": ""}) 
                            value["compare_timestamps"].append(startTimeStamp) #add timestamp each time 
        
                else:
                    detected_barcodes.append({'barcode': myData, 'timestamps': [{'start': startTimeStamp, "end": "" }], 'compare_timestamps': [startTimeStamp]})
    return detected_barcodes



