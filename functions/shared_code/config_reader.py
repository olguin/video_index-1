from urllib.request import urlopen
from urllib.request import HTTPError
import json
import logging

class Configuration():

    @classmethod
    def from_url(cls, container_url):
        return Configuration(Configuration.read_configuration(container_url))

    @classmethod
    def read_configuration(cls, container_url):
        if(container_url == None):
            return None

        try:
            config_file = urlopen(f"{container_url}/config.json")
            config_json = config_file.read()
            return json.loads(config_json)
        except HTTPError as e:
            logging.error(f"Error {e} reading configuration")
            return None

    def __init__(self, configuration):
        self.configuration = configuration

    def getLanguage(self):
        if(self.configuration == None):
            return "en"
        else:
            return self.configuration.get("language", "en")

    def filterSectionsByConfigInRecord(self, record):
        sections = [*record]
        for section in sections:
            if(not self.isSectionEnabled(section)):
                    del record[section]
        if("match_count" in record):
            counts = [*record["match_count"]]
            for count in counts:
                if(not self.isSectionEnabled(count)):
                        del record["match_count"][count]


    def isSectionEnabled(self, section):
        if(self.configuration == None):
            return True
        else:
            services = self.configuration["services"]["video"]
            return (section in services) or self.alwaysIncludedSection(section)

    def alwaysIncludedSection(self, section):
        return section in ["header", "path", "id", "match_count"]


