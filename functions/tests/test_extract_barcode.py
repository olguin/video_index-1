import datetime
from QrScanner.extract_barcodes import *
import pytest
import json
import os
from shared_code.configuration_file import ConfigurationFile as ConfigurationFile


def test_extract_barcodes():
    configuration = ConfigurationFile(
        {
        "index_provider": "Azure",
        "field_service"  : "D365",
        "search_parameters": [ {"maximum_video_count_in_search_results": 100 }],
        "services" : {
                            "video": ["barcodes" , "brands" , "faces" , "header" , "keywords" , "labels" , "metadata" , "ocr" , "topics" , "transcripts" ]
                    },

            "metadata" : {},
            "language": "en"
        },
        "file_name"
    )
    extract_barcodes(f"{os.getcwd()}/tests/barcode_sampled.mp4", "123456", configuration)

def test_extract_barcodes_no_barcodes():
    configuration = ConfigurationFile(
        {
        "index_provider": "Azure",
        "field_service"  : "D365",
        "search_parameters": [ {"maximum_video_count_in_search_results": 100 }],
        "services" : {
                            "video": ["barcodes" , "brands" , "faces" , "header" , "keywords" , "labels" , "metadata" , "ocr" , "topics" , "transcripts" ]
                    },

            "metadata" : {},
            "language": "en"
        },
        "file_name"
    )
    extract_barcodes(f"{os.getcwd()}/tests/zZhIwsylKkU_99_101.mp4", "123456", configuration)

def test_extract_barcodes_exception():
    configuration = ConfigurationFile(
        {
        "index_provider": "Azure",
        "field_service"  : "D365",
        "search_parameters": [ {"maximum_video_count_in_search_results": 100 }],
        "services" : {
                            "video": ["barcodes" , "brands" , "faces" , "header" , "keywords" , "labels" , "metadata" , "ocr" , "topics" , "transcripts" ]
                    },

            "metadata" : {},
            "language": "en"
        },
        "file_name"
    )
    extract_barcodes(f"{os.getcwd()}/tests/does_not_exist.mp4", "123456", configuration)


