import time, json, tqdm
from browsermobproxy import Server
from selenium import webdriver
from urllib import parse
from src.util.regexps import MAP_TILE_REGEX

# run a proxy server to capture requests
server = Server("D:\\PROJECTS\\_imagegeo\\browsermob-proxy\\bin\\browsermob-proxy")
server.start()

# proxy client
proxy = server.create_proxy()

# add proxy to browser
options = webdriver.ChromeOptions()
options.add_argument('--proxy-server={}'.format(proxy.proxy))
options.add_argument('ignore-certificate-errors')

# create browser driver
d = webdriver.Chrome(options=options)

# define haars dict
haars = {}

def load_page(url):
    d.get(url)

# parse urls (capture haars)
for url in tqdm.tqdm(open("mapshrefs.txt", "r")):
    if url.startswith("#"): continue
    
    proxy.new_har()
    url = url.strip()
    load_page(url)
    time.sleep(10)

    haars[url] = proxy.har

# stop proxy
server.stop()

# dump haars
with open("parseddata/haars.json", "w") as f:
    json.dump(haars, f, indent=4)

# define panoramas arr
panoramas = []

# process captured haars
for url, har in tqdm.tqdm(haars.items()):
    for entry in har["log"]["entries"]:
        if MAP_TILE_REGEX.fullmatch(entry["request"]["url"]):
            qs = parse.parse_qs(parse.urlparse(url).query)
            panoramas.append({
                "point": qs["panorama[point]"][0],
                "id": entry["request"]["url"].split("/")[-2],
                "url": url,
            })
            break

print("Found", len(panoramas), "panorama(s) (wrote to `panoramas.json`)")
with open("parseddata/panoramas.json", "w") as f:
    json.dump(panoramas, f, indent=4)
