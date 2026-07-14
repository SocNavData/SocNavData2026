import js
import json
import random

try:
    from pyodide.http import open_url
except Exception:
    open_url = None

MAX_TASKS = 28-2
FIXED_DESCRIPTIONS_FILE = "fixed_descriptions.json"
_FIXED_DESCRIPTIONS_CACHE = None

FIXED_TASKS = [
    # these are the control questions that will be fixed in the survey, to ensure data quality. The format is (position_in_survey, video_id, description)
    # keeping in mind that the position is 0-indexed and there is an extra control question, so position 4 means the 6th video shown to the user
    # the descriptions are assigned in the fixed_descriptions.json file, so they can be easily updated without changing the code.
    # The descriptions in the json file should match the video_id, 
    # but we provide a default description here as well in case the json file is not found or does not contain the correct entries.
    # The other indices, if not found in the json file, will be generated randomly from the all_contexts.txt file, so they can be easily changed by updating that file without changing the code.
    #(0, 13, "A robot is being nice"),
    (4, 126, "First control question: A robot is trying to locate the source of a noise in a library."),
    (9, 318, "Second control question: A robot is navigating as part of a delivery task in a museum."),
    (11, 1083, "Third control question: A robot is trying to locate the glasses of a patient in a hospital."),
    #(13, 1095, "A robot is exploring around looking for people interested in its services."),
    #(14, 999, "A robot is exploring around looking for people interested in its services."),
    (18, 1012, "Fourth control question: A hotel robot is inspecting the floor to ensure it's safe to walk."),
    #(24, 1040, "A robot is exploring around looking for people interested in its services."),
    (20, 1054, "Fifth control question: A drug delivery robot is working in a hospital."),
]


def get_fixed_task_video_ids():
    return {video_id for _, video_id, _ in FIXED_TASKS}

def _parse_indices_text(text):
    text = text.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            indices = []
            for item in parsed:
                try:
                    indices.append(int(item))
                except (TypeError, ValueError):
                    continue
            return indices
        text = str(parsed)
    except Exception:
        pass

    clean = (
        text.replace("[", " ")
        .replace("]", " ")
        .replace(",", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )
    parts = [p for p in clean.split(" ") if p]
    indices = []
    for part in parts:
        try:
            indices.append(int(part))
        except ValueError:
            continue
    return indices

def _load_fixed_descriptions():
    global _FIXED_DESCRIPTIONS_CACHE
    if _FIXED_DESCRIPTIONS_CACHE is not None:
        return _FIXED_DESCRIPTIONS_CACHE

    fixed = None
    if open_url is not None:
        for url in (f"/static/{FIXED_DESCRIPTIONS_FILE}", f"/{FIXED_DESCRIPTIONS_FILE}"):
            try:
                response = open_url(url).read()
                if isinstance(response, bytes):
                    response = response.decode("utf-8", errors="replace")
                fixed = json.loads(response)
                break
            except Exception:
                fixed = None

    if fixed is None:
        try:
            with open(FIXED_DESCRIPTIONS_FILE, "r") as fd:
                fixed = json.load(fd)
        except FileNotFoundError:
            fixed = None
        except Exception:
            fixed = None

    if isinstance(fixed, dict):
        normalized = {}
        for key, value in fixed.items():
            try:
                key_int = int(key)
            except (TypeError, ValueError):
                continue
            if isinstance(value, str):
                normalized[key_int] = value
        fixed = normalized
    else:
        fixed = None

    _FIXED_DESCRIPTIONS_CACHE = fixed
    return fixed

def get_tasks_and_probabilities():
    with open("all_contexts.txt", "r") as fd:
        lines = fd.readlines()
    
    # Read indices from the server if possible, fallback to local file
    last_indices = []
    if open_url is not None:
        try:
            response = open_url("/indices.txt").read()
            if isinstance(response, bytes):
                response = response.decode("utf-8", errors="replace")
            last_indices = _parse_indices_text(response)
        except Exception:
            last_indices = []

    if not last_indices:
        try:
            with open("indices.txt", "r") as fd:
                last_indices = _parse_indices_text(fd.read())
        except FileNotFoundError:
            # indices.txt may not exist on first load, that's okay
            js.console.log("Warning: indices.txt not found, will generate random sequence")

    tasks = []
    dict_counts = { "assign":0, "battery":0, "routine":0, "delivery":0, "collection":0, "explore":0, "clean":0, "lab":0, "fire":0 }

    for line in lines:
        if "assign" in line:
            dict_counts["assign"] += 1
        elif "battery" in line:
            dict_counts["battery"] += 1
        elif "routine tasks" in line:
            dict_counts["routine"] += 1
        elif "delivery" in line:
            dict_counts["delivery"] += 1
        elif "collection" in line:
            dict_counts["collection"] += 1
        elif "explores" in line:
            dict_counts["explore"] += 1
        elif "clean" in line:
            dict_counts["clean"] += 1
        elif "lab" in line:
            dict_counts["lab"] += 1
        elif "fire" in line:
            dict_counts["fire"] += 1
        else:
            print(line)
            break
        tasks.append(line)

    # Define the categories and their corresponding values
    categories = []
    counts = []
    for k,v in dict_counts.items():
        categories.append(k)
        counts.append(v)
        js.console.log(f"{k} --> {v}")
    

    probabilities = [ 1./v for v in counts ]
    probabilities[categories.index("lab")] /= 4   # Lower these manually
    probabilities[categories.index("fire")] /= 4  # Lower these manually

    for i in range(len(probabilities)):
        js.console.log(f"{categories[i]} --> {probabilities[i]}")
    return tasks, categories, probabilities, last_indices


def should_we_accept(line, categories, probabilities):
    if "assign" in line:
        category = "assign"
    elif "battery" in line:
        category = "battery"
    elif "routine" in line:
        category = "routine"
    elif "delivery" in line:
        category = "delivery"
    elif "collection" in line:
        category = "collection"
    elif "explores" in line:
        category = "explore"
    elif "clean" in line:
        category = "clean"
    elif "lab" in line:
        category = "lab"
    elif "fire" in line:
        category = "fire"
    else:
        js.console.log(f"Unknown category for task: {line}")
        return False

    index = categories.index(category)
    probability = probabilities[index]

    sample = random.random()
 
    if probability >= sample:
        return True
    else:
        return False

def generate_descriptions():
    tasks, categories, probabilities, _ = get_tasks_and_probabilities()

    descriptions = []
    while len(descriptions) < MAX_TASKS:
        accepted = False
        while accepted is False:
            task = random.randint(0, len(tasks)-1)
            accepted = should_we_accept(tasks[task], categories, probabilities)
        descriptions.append(tasks[task])

    return descriptions


def build_descriptions_from_indices(indices):
    fixed = _load_fixed_descriptions()
    if not fixed:
        return generate_descriptions()

    descriptions = []
    for idx in indices:
        if idx is None:
            descriptions.append("")
            continue
        try:
            idx_int = int(idx)
        except (TypeError, ValueError):
            descriptions.append("")
            continue
        desc = fixed.get(idx_int)
        if not desc:
            js.console.log(f"Missing fixed description for video {idx_int}")
            desc = ""
        descriptions.append(desc)
    return descriptions


def get_description_for_index(video_id, default=""):
    fixed = _load_fixed_descriptions()
    if not fixed:
        return default
    try:
        idx_int = int(video_id)
    except (TypeError, ValueError):
        return default
    return fixed.get(idx_int, default)



def fix_fixed_tasks(structure):
    indices = structure.get("indices")
    descriptions = structure.get("descriptions")
    for position, video_id, desc in FIXED_TASKS:
        if indices is not None and position < len(indices):
            indices[position] = video_id
        if descriptions is not None and position < len(descriptions):
            descriptions[position] = get_description_for_index(video_id, desc)
    #structure["descriptions"][7] = "A robot is trying to locate the source of a noise in a library."
    ##  2 [ R E P E A T E D --  9]
    #structure["indices"][11] = 2007
    #structure["descriptions"][11] = "A robot is navigating as part of a delivery task in a museum."
    ##  3 [ R E P E A T E D -- 10]
    #structure["indices"][13] = 1007
    #structure["descriptions"][13] = "An office assistant robot keeps track of who is in the office today."
    ##  4 [ R E P E A T E D -- 11]
    #structure["indices"][17] = 7
    #structure["descriptions"][17] = "A hotel robot is inspecting the floor to ensure it's safe to walk."
    ##  5 [ R E P E A T E D -- 12]
    #structure["indices"][19] = 302
    #structure["descriptions"][19] = "A drug delivery robot is working in a hospital."
    ##  6
    #structure["indices"][23] = 1302
    #structure["descriptions"][23] = "A museum robot roams around looking for people interested in its services."
    ##  7
    #structure["indices"][29] = structure["indices"][7]
    #structure["descriptions"][29] = structure["descriptions"][7]
    ##  8
    #structure["indices"][31] = 2302
    #structure["descriptions"][31] = "A robot is performing routine tasks in an office."
    ##  9
    #structure["indices"][37] = structure["indices"][11]
    #structure["descriptions"][37] = structure["descriptions"][11]
    ## 10
    #structure["indices"][41] = structure["indices"][13]
    #structure["descriptions"][41] = structure["descriptions"][13]
    ## 11
    #structure["indices"][43] = structure["indices"][17]
    #structure["descriptions"][43] = structure["descriptions"][17]
    ## 12
    #structure["indices"][47] = structure["indices"][19]
    #structure["descriptions"][47] = structure["descriptions"][19]
    ## 13
    #structure["indices"][53] = 3102
    #structure["descriptions"][53] = "A museum guide robot has been asked to go to the goal shown, with no additional context."
    ## 14
    #structure["indices"][59] = 2002
    #structure["descriptions"][59] = "A lab assistant robot is looking for potential hazards in its environment."
    ## 15
    #structure["indices"][61] = 1002
    #structure["descriptions"][61] = "A cleaning robot working in a hospital is looking for dirty spots to clean."
    ## 16
    #structure["indices"][67] = 2
    #structure["descriptions"][67] = "The robot is trying to locate the glasses of a patient in a hospital."
    ## 17
    #structure["indices"][71] = 3094
    #structure["descriptions"][71] = "A hospital assistant robot has been asked to go to the goal, with no additional context."
    ## 18
    #structure["indices"][73] = 2894
    #structure["descriptions"][73] = "An idle robot working in a museum goes to recharge its battery. It has 13% battery left."
    ## 19
    #structure["indices"][79] = 1879
    #structure["descriptions"][79] = "A assistant robot is performing routine tasks in a restaurant."
    ## 20
    #structure["indices"][83] = 834
    #structure["descriptions"][83] = "A warehouse robot is moving around while inspecting the air quality."

