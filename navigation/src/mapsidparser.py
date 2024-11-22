import regex, time, os, json
from browsermobproxy import Server
from selenium import webdriver
from urllib import parse

MAP_TILE_REGEX = r"https:\/\/pano.maps.yandex.net\/[a-z0-9A-Z]+\/[0-9][0-9]?.[0-9][0-9]?.[0-9][0-9]?+"
MAP_TILE_REGEX = regex.compile(MAP_TILE_REGEX)

server = Server("D:\\PROJECTS\\_imagegeo\\browsermob-proxy\\bin\\browsermob-proxy")
server.start()

proxy = server.create_proxy()

options = webdriver.ChromeOptions()
options.add_argument('--proxy-server={}'.format(proxy.proxy))
options.add_argument('ignore-certificate-errors')

d = webdriver.Chrome(options=options)

haars = {}

def load_page(url):
    d.get(url)

for url in open("mapshrefs.txt", "r"):
    if url.startswith("#"): continue
    
    proxy.new_har()
    url = url.strip()
    print(url)
    load_page(url)
    time.sleep(10)

    haars[url] = proxy.har

server.stop()

with open("parseddata/haars.json", "w") as f:
    json.dump(haars, f, indent=4)

haars: dict[str, dict] = json.load(open("parseddata/haars.json", "r"))
panoramas = []

for url, har in haars.items():
    for entry in har["log"]["entries"]:
        if MAP_TILE_REGEX.fullmatch(entry["request"]["url"]):
            qs = parse.parse_qs(parse.urlparse(url).query)
            panoramas.append({
                "point": qs["panorama[point]"][0],
                "id": entry["request"]["url"].split("/")[-2],
                "url": url,
            })
            break

print("Found", len(panoramas), "panorama(s)\n(wrote to `panoramas.json`)")
with open("parseddata/panoramas.json", "w") as f:
    json.dump(panoramas, f, indent=4)
