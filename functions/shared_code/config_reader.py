from urllib.request import urlopen
from urllib.request import HTTPError
import json
import logging

class Configuration():

    def __init__(self, container_url):
        self.configuration = self.read_configuration(container_url)

    def read_configuration(self, container_url):
        if(container_url == None):
            return None

        try:
            config_file = urlopen(f"{container_url}/config.json")
            config_json = config_file.read()
            return json.loads(config_json)
        except HTTPError as e:
            logging.error(f"Error {e} reading configuration")
            return None


    def getLanguage(self):
        if(self.configuration == None):
            return "en"
        else:
            return self.configuration["language"]

    def filterSectionsByConfigInRecord(self, record):
        sections = [*record]
        for section in sections:
            if(not self.isSectionEnabled(section)):
                    del record[section]


    def isSectionEnabled(self, section):
        if(self.configuration == None):
            return True
        else:
            services = self.configuration["services"]["video"]
            return (section in services) or self.alwaysIncludedSection(section)

    def alwaysIncludedSection(self, section):
        return section in ["header", "path", "id", "match_count"]


