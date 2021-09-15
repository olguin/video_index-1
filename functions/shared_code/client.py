from video_indexer_tools import *
from config_reader import Configuration as Configuration 

path = "https://demosc.blob.core.windows.net/demo-container/barcode-testing.mp4"
result = get_video_info(path, Configuration.from_url(os.path.dirname(path)))
print(result)
