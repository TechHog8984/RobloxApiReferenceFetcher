import requests, os, re;
from json import loads as jsonDecode;
from json import dumps as jsonEncode;
from threading import Thread;

roblox_versions_path = f"{os.getenv('localappdata')}\\Roblox\\versions\\";
version_path = roblox_versions_path + os.listdir(roblox_versions_path)[0]
document_path = version_path + "\\content\\api_docs\\en-us.json";

with open(document_path) as file:
    decoded_document = jsonDecode(file.read());
    file.close();

class_list = [];
for key in decoded_document:
    value = decoded_document[key];
    learn_more_link = value.get("learn_more_link");
    if learn_more_link:
        if ("https://create.roblox.com/docs/reference/engine/classes/" in learn_more_link) and ("#" not in learn_more_link) and ("CSGOptions" not in learn_more_link):
            class_list.append(key.replace("@roblox/globaltype/", ""));

# build_id = input("BUILD ID: ");
def getBuildId():
    request = requests.get("https://create.roblox.com/docs/reference/engine/datatypes/Axes");
    text = request.text;
    match = re.search('"buildId":"(\w+)"', text);
    return match.group(1);

build_id = getBuildId();

def fetchClass(class_name):
    url = f"https://create.roblox.com/docs/_next/data/{build_id}/reference/engine/classes/{class_name}.json";
    return requests.get(url);
def fetchClassJson(class_name):
    return fetchClass(class_name).json().get("pageProps").get("data");

api_class_lookup = {};
class ApiClass:
    def __init__(self, class_name):
        self.name = class_name;
        self.json = fetchClassJson(class_name);
        self.api_reference = self.json.get("apiReference");
        self.properties = self.api_reference.get("properties");
        self.inherits = self.api_reference.get("inherits");

        api_class_lookup[class_name] = self;

    def getUniqueProperties(self):
        unique_properties = [];
        for prop in self.properties:
            name = prop.get("name");
            if name.startswith(self.name + "."):
                name = name[len(self.name) + 1:];

            unique_properties.append({
                "name": name,
                "type": prop.get("type"),
                "tags": prop.get("tags") or ""
            });

        return unique_properties;

    def getAllProperties(self):
        all_properties = self.getUniqueProperties();
        for class_name in self.inherits:
            for prop in apiClass(class_name).getAllProperties():
                all_properties.append(prop);

        return all_properties;

def apiClass(class_name):
    if api_class_lookup.get(class_name):
        return api_class_lookup[class_name];
    return ApiClass(class_name);

result_json = {};
def addToResult(class_name):
    print("fetching " + class_name);
    try:
        api_class = apiClass(class_name);
        result_json[class_name] = {"inherits": api_class.inherits, "properties": api_class.getUniqueProperties()};
    except Exception as e:
        print("failed to fetch " + class_name + ": " + str(e));

threads = [];
for class_name in class_list:
    threads.append(Thread(target=addToResult, args=[class_name]));

for thread in threads:
    thread.start();
for thread in threads:
    thread.join();

with open("result.json", "w") as result_file:
    result_file.write(jsonEncode(result_json));
    result_file.close();
