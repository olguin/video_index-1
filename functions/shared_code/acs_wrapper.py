import logging
import requests
import json

def get_highlights(record):
    return record.get("@search.highlights", {})

def match_with_highligts(metadata_element, highlights):
    for highlight in highlights:
        clean_highlight = highlight.replace("<em>","").replace("</em>","")
        if(metadata_element["value"] == clean_highlight):
            return {"key": metadata_element["key"], "value": highlight}
    return metadata_element

def match_metadata(metadata, highlights):
    matched_metadata=[]
    for metadata_element in metadata:
        matched_metadata.append(match_with_highligts(metadata_element, highlights))
    return matched_metadata

def find_text_matching_highlights(current_field,recordId,text, highlights):
    if(text == None):
        return None
    matching_highlights = []
    for highlight in highlights:
        clean_highlight = highlight.replace("<em>","").replace("</em>","")
        if(clean_highlight in text):
            matching_highlights.append(highlight)
    if(len(matching_highlights) == 0):
        if(recordId != None):
            return text
        else:
            return None
    else:
        if(type(text) == type([])):
            return matching_highlights
        else:
            return matching_highlights[0]

def addTitles(config, search_result):
    titles = {
        "en": {
            "barcodes": "Barcodes",
            "transcripts": "Transcript",
            "ocr": "On-Screen Text",
            "keywords": "Keywords",
            "topics": "Topics",
            "faces": "Faces",
            "labels": "Labels",
            "brands": "Brands",
            "header": "Video information",
            "metadata": "Video metadata"
        },
        "sp": {
            "barcodes": "Códigos de Barra",
            "transcripts": "Transcripción",
            "ocr": "Texto en pantalla",
            "keywords": "Palabras clave",
            "topics": "Temas",
            "faces": "Rostros",
            "labels": "Etiquetas",
            "brands": "Marcas",
            "header": "Información del video",
            "metadata": "Metadata del video"
        }
    }
    search_result["titles"] = titles[config.getLanguage()]

def process_highlights(record,recordId, field_path, highlights, matches_count, root_field):
    current_field = field_path[0]
    subrecord = record[current_field]
    if(len(field_path) == 1):
        matching_highlight = find_text_matching_highlights(current_field,recordId,subrecord, highlights)
        if(matching_highlight != None):
            record[current_field] = matching_highlight
            if("<em>" in matching_highlight):
                current_count = matches_count.get(root_field,0)
                if("timestamps" in record):
                    matches_count[root_field] = current_count + len(record["timestamps"])
                else:
                    matches_count[root_field] = current_count + 1
            return record
    else:
        if(type(subrecord) == type({})):
            return process_highlights(subrecord, recordId, field_path[1:], highlights, matches_count, root_field)
        else:
            if(current_field == "metadata"):
                return match_metadata(subrecord, highlights)

            processed_list = []
            for record_elem in subrecord:
                highlighted_element = process_highlights(record_elem, recordId, field_path[1:], highlights, matches_count, root_field)
                if(highlighted_element != None):
                    processed_list.append(highlighted_element)
            return processed_list

def add_highlighted_subrecord(processed_record, field_path, highlighted_subrecord):
    current_field = field_path[0]
    if(len(field_path) <= 2):
        processed_record[current_field] = highlighted_subrecord
    else:
        processed_record[current_field] = processed_record.get(current_field, {})
        add_highlighted_subrecord(processed_record[current_field], field_path[1:], highlighted_subrecord)

def copy_header(record, processed_record):
    processed_record["header"] = processed_record.get("header", {})
    fields = ["creation_date", "description", "name", "owner", "thumbnail"]
    for field in fields:
        if(not field in processed_record["header"]):
            processed_record["header"][field] = record["header"][field]
    
def copy_metadata(record, processed_record):
    if(not "metadata" in processed_record):
        processed_record["metadata"] = record["metadata"]


def get_match_count(isStarSearch, values):
    count = 0
    for value in values:
        if("value" in value):
            text = value["value"]
        else:
            text = value["text"]
        if("<em>" in text or isStarSearch):
            if("timestamps" in value):
                count = count + len(value["timestamps"])
            else:
                count = count + 1

    return count

    
def add_missing_match_counts(processed_record,match_count, isStarSearch):
    for field,values in processed_record.items():
        if(not (field in match_count) and type(values) == type([])):
            match_count[field] = get_match_count(isStarSearch, values)
    processed_record["match_count"] = match_count
    return processed_record

def process_record(record, recordId):
    processed_record = {}
    matches_count = {}
    record_highlights = get_highlights(record)
    for field, highlights in record_highlights.items():
        field_path = field.split("/")
        root_field=field_path[0]
        highlighted_subrecord = process_highlights(record,recordId,field_path, highlights, matches_count, root_field)
        add_highlighted_subrecord(processed_record, field_path, highlighted_subrecord)
    if(recordId != None):
        for section in record:
            if(not section in processed_record):
                processed_record[section] = record[section]
    copy_header(record, processed_record)
    copy_metadata(record, processed_record)
    processed_record["id"] = record["id"]
    add_missing_match_counts(processed_record,matches_count, False)
    processed_record["match_count"] = matches_count
    processed_record["path"] = record["path"]


    return processed_record

def get_json(my_file):
    with open(my_file, newline='') as json_file:
        data = json.load(json_file) 
    return data

def run_search(service,index,key,api_version,params):
    searchIndexURL=f"https://{service}.search.windows.net/indexes/{index}/docs/search?api-version={api_version}"
    res = requests.post(searchIndexURL,data=json.dumps(params),headers={"api-key":key, "Content-Type": "application/json"})
    response=res.content.decode("utf-8")
    try:
        json.loads(response)
    except:
        logging.error(f"response '{response}' is not valid JSON")
    return response

def get_highlighted_fields():
    fields = [
        "path",
        "barcodes/text",
        "transcripts/text",
        "ocr/text",
        "keywords/text",
        "topics/text", 
        "topics/reference",
        "topics/referenceURL",
        "topics/referenceType",
        "faces/text",
        "labels/text",
        "brands/text",
        "brands/reference",
        "brands/referenceURL",
        "brands/description",
        "header/owner",
        "header/creation_date",
        "header/name",
        "header/description",
        "header/thumbnail",
        "metadata/value"]
    return ",".join(fields)

def clean_params(params):
   cleaned_params = dict(params) 
   del cleaned_params["service"]
   del cleaned_params["key"]
   del cleaned_params["api_version"]
   del cleaned_params["index"]
   del cleaned_params["container"]
   if("id" in cleaned_params):
    del cleaned_params["id"]
   cleaned_params["highlight"] = get_highlighted_fields()
   cleaned_params["queryType"] = "full"

   return cleaned_params

def filterSectionsByConfig(records, config):
    for record in records:
        config.filterSectionsByConfigInRecord(record)

def appendProcessedRecord(processed_records,record,recordId):
    if(recordId != None and record["id"] != recordId):
        return 

    processed_records.append(process_record(record, recordId))


def search_from_json(params, config):
    recordId = params.get("id", None)
    search_result = json.loads(run_search(params["service"],params["index"],params["key"],params["api_version"],clean_params(params)))
    if("error" in search_result or not ("value" in search_result)):
        return search_result

    processed_records = []
    if(params["search"] != "*"):
        for record in search_result["value"]:
            appendProcessedRecord(processed_records,record,recordId)
    else:
        for record in search_result["value"]:
            processed_records.append(add_missing_match_counts(record,{},True))

    filterSectionsByConfig(processed_records, config)

    search_result["value"] = processed_records
    addTitles(config, search_result)
    return search_result

