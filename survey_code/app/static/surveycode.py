import js
import json
import random
import asyncio

import pyodide

from slider import Slider
import tasks


MAX_ANSWERS = 26
MAX_VIDEOS = 1134


videoSource1 = js.document.getElementById('myVideoSource1')
#videoSource2 = js.document.getElementById('myVideoSource2')
indices_txt = js.document.getElementById('indices_txt')
video = js.document.getElementById('myVideo')
description = js.document.getElementById('myDescription')
#canvas = js.document.getElementById('myCanvas')
#canvas_saf = js.document.getElementById('myCanvasSafety')
#canvas_friend = js.document.getElementById('myCanvasFriendliness')
#canvas_natural = js.document.getElementById('myCanvasNaturalness')
#canvas_comf = js.document.getElementById('myCanvasComfort')


prev_btn = js.document.getElementById('prev-btn')
next_btn = js.document.getElementById('next-btn')
send_btn = js.document.getElementById('send-btn')
age = js.document.getElementById('age')
country = js.document.getElementById('country')

structure = {
    'answers': None,
    'indices': None,
    'descriptions': None,
    'country': None,
    'age': None,
    'gender': None
}

# 1. Configuration: (Canvas ID, Dictionary Key, Display Name on Screen)
SLIDER_CONFIG = [
    ('myCanvasSafety', 'safety', 'Safety'),
    ('myCanvasPredictability', 'predictability', 'Predictability'),
    ('myCanvasNaturalness', 'naturalness', 'Naturalness'),
    ('myCanvasSocialness', 'socialness', 'Socialness'),
    ('myCanvasOverall', 'overall', 'Overall score')
]

expected_metrics = [metric for _, metric, _ in SLIDER_CONFIG]
sliders = []

# 2. Get the empty container from the HTML
container = js.document.getElementById('slider-container')

# 3. Generate the UI and initialize the Sliders dynamically
for canvas_id, metric, display_name in SLIDER_CONFIG:
    
    # Create the label <p><strong>Name:</strong></p>
    label = js.document.createElement("p")
    label.style.textAlign = "center"
    label.style.marginBottom = "5px"
    label.style.marginTop = "20px"
    
    # --- ADD THESE TWO LINES FOR MODERN TEXT ---
    label.style.fontFamily = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    label.style.color = "#334155" # Dark slate
    
    label.innerHTML = f"<strong>{display_name}</strong>"
    container.appendChild(label)
    
    # Create the <canvas>
    canvas = js.document.createElement("canvas")
    canvas.id = canvas_id
    canvas.width = 340
    canvas.height = 60
    canvas.style.backgroundColor = "transparent" # Let the page background show through
    canvas.style.touchAction = "none"
    canvas.style.display = "block"
    canvas.style.margin = "0 auto"
    container.appendChild(canvas)
    
    # Initialize the Python Slider object with this newly created canvas
    sliders.append(Slider(canvas, structure, metric, expected_metrics))

def reload_video_function(structure):
    js.console.log("Reload!")
    question_index = int(js.eval("questionIndex"))

    if not structure.get("indices") or not structure.get("descriptions"):
        js.console.log("Missing indices or descriptions")
        return

    if question_index < 0 or question_index >= len(structure["indices"]) or question_index >= len(structure["descriptions"]):
        js.console.log(f"question_index out of range: {question_index}")
        return
    
    text = structure["descriptions"][question_index]
    description.innerText = text
    
    # Target the img element directly
    #video_element = js.document.getElementById('myVideo')
    
    # Get the filename (adjust logic if your filenames change per question)
    # 1. Get the actual random video ID assigned to this question
    video_id = str(structure["indices"][question_index])


    #gif_path = f"/static/videos/video_SACSON/{video_id.zfill(9)}.webm"
    gif_path_mp4 = f"/static/videos/complete_indexed_videos/{video_id.zfill(9)}.mp4"
    videoSource1.src = gif_path_mp4
    #videoSource2.src = gif_path_mp4
    video.load()  # Reload the video element to apply the new source
    # Adding a timestamp ensures the GIF starts from frame 1
    #video_element.src = f"{gif_path}?t={js.Date.now()}"
    
    # Update counter logic...
    count = js.document.getElementById('myCounter')
    if question_index <= 25:
        count.innerHTML = f"<span style=\"color: #440000\">{question_index+1}/26 (up to {MAX_ANSWERS})<span>"
    else:
        count.innerHTML = f"<span style=\"color: #007700\">{question_index+1}/2 (up to {MAX_ANSWERS})<span>"

def getTouchPos(canvas, touchEvent):
    rect = canvas.getBoundingClientRect()
    touch = touchEvent.touches.item(0)
    return touch.clientX - rect.left, touch.clientY - rect.top

def draw(event=None):
    for slider in sliders:
        slider.draw(event)

def maybe_show_value():
    question_index = int(js.eval("questionIndex"))
    if question_index in structure["answers"].keys():
        # print(structure["answers"].keys())
        js.eval(f"video_watched = 1;")
        for slider in sliders:
            # Safely get the value if it exists, otherwise set to None
            val = structure["answers"][question_index].get(slider.metric_name)
            if val is not None:
                slider.set_value(val)
            else:
                slider.value = None
    else:
        js.console.log(f"{question_index} not in structure")
        for slider in sliders:
            slider.value = None
    draw()


def load_data(structure):
    
    data = js.window.localStorage.getItem('socnav_data')
    if data:
        # print("There was data saved!")
        data = json.loads(data)
        structure["indices"] = data["indices"]
        structure["descriptions"] = data["descriptions"]
        structure["answers"]  = data["answers"]

        try:
            structure["age"] = data["age"]
        except:
            structure["age"] = 18
            js.alert("There was an issue recovering the demographic information. Please go to the demographic page before submitting the data.")
        js.document.getElementById("age").value = structure["age"]
        js.console.log("age", structure["age"])

        try:
            structure["country"] = data["country"]
        except:
            structure["country"] = "GB"
        js.document.getElementById("country").value = structure["country"]
        js.console.log("country", structure["country"])

        try:
            structure["gender"] = data["gender"]
        except:
            structure["gender"] = "not-say"
        js.document.getElementById("gender").value = structure["gender"]
        js.console.log("gender", structure["gender"])



        for k in [kk for kk in structure["answers"].keys()]:
            structure["answers"][int(k)] = structure["answers"][k]
            del structure["answers"][k]
        # print('answers', structure["answers"])
        question = int(data['questionIndex'])
        # print('question', question)
        js.eval(f"currentPage = {data['currentPage']};")
        js.eval(f"questionIndex = {question};")
        if question in structure["answers"].keys():
            # print("si la")
            js.eval(f"answer_set = 1;")
            js.eval(f"video_watched = 1;")
        else:
            # print("no la")
            js.eval(f"answer_set = 0;")
        js.eval(f"reload_video = 1;")
        js.eval("document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));")
        act = js.document.getElementById(f"page-{data['currentPage']}")
        act.classList.add('active')
        reload_video_function(structure)
        return True
    
    # reload_video_function(structure)
    return False


def save_data(structure):

    try:
        js.console.log("age" + structure["age"])
        js.console.log("country" + structure["country"])
        js.console.log("gender" + structure["gender"])
    except:
        js.console.log("cannot show stuff yet?")
        js.console.log(js.eval("currentPage"))

    data = {
        "indices": structure["indices"],
        "descriptions": structure["descriptions"],
        "answers": structure["answers"],
        "age": structure["age"],
        "gender": structure["gender"],
        "country": structure["country"],
        "currentPage": int(js.eval("currentPage")),
        "questionIndex": int(js.eval("questionIndex")),
        "answer_set": int(js.eval("answer_set")),
        "reload_video": int(js.eval("reload_video")),
        "video_watched": int(js.eval("video_watched"))
    }
    js.window.localStorage.setItem('socnav_data', json.dumps(data))




if load_data(structure) is True:
    js.eval("showPage(currentPage);")
    question = int(js.eval(f"questionIndex;"))
    maybe_show_value()
else:
    # Try multiple locations for indices.txt (workspace storage preferred)
    #possible_paths = [
        #"/workspaces/hunavsim_devcontainer/storage/indices.txt",
        #"static/indices.txt",
    _,_,_,lista = tasks.get_tasks_and_probabilities()
    #if lista is None:
    print("Could not find indices file in any known location. Generating random indices.")
    structure["answers"] = {}
    structure["indices"] = [None] * MAX_ANSWERS

    #structure["indices"] = None
    structure["descriptions"] = tasks.generate_descriptions()
    tasks.fix_fixed_tasks(structure)

    exclude_ids = tasks.get_fixed_task_video_ids()
    available_indices = [
        i for i in range(1, MAX_VIDEOS + 1)
        if i not in exclude_ids
    ]
    random_needed = sum(1 for idx in structure["indices"] if idx is None)
    random_indices = random.sample(available_indices, random_needed)

    random_iter = iter(random_indices)
    for i, idx in enumerate(structure["indices"]):
        if idx is None:
            structure["indices"][i] = next(random_iter)

    control_index = random.choice(random_indices) if random_indices else random.choice(structure["indices"])

    structure["indices"].insert(0, control_index)
    structure["indices"].append(control_index)
    structure["descriptions"].insert(0, "This is a control video to check if you are paying attention. Please rate it as you would normally do, there is no right or wrong answer for this one.")
    structure["descriptions"].append("This is a control video to check if you are paying attention. Please rate it as you would normally do, there is no right or wrong answer for this one.")
    #else:
    #    #print(lista)
    #    try:
    #        payload = json.dumps({"label": "lista", "value": lista})
    #        js.eval(
    #            "fetch('/log', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: "
    #            + json.dumps(payload)
    #            + "})"
    #        )
    #    except Exception as e:
    #        js.console.log(f"Failed to log lista to server: {e}")
    #    # If we loaded indices, keep existing answers empty and set indices from file
    #    structure["answers"] = {}
    #    # attempt to parse as JSON array or comma-separated string
    #    structure["indices"] = [random.randint(1, MAX_VIDEOS) for _ in range(MAX_ANSWERS)]
    #    ## exclude the indices that appear in the file from the random generation
    #    reduced_lista = [x for x in lista[:MAX_ANSWERS] if x > 1]
    #    try:
    #        payload = json.dumps({"label": "reduced_lista", "value": reduced_lista})
    #        js.eval(
    #            "fetch('/log', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: "
    #            + json.dumps(payload)
    #            + "})"
    #        )
    #    except Exception as e:
    #        js.console.log(f"Failed to log reduced_lista to server: {e}")
    #    exclude = set(reduced_lista)
    #    structure["indices"] = [idx for idx in structure["indices"] if idx not in exclude]
    #    try:
    #       payload = json.dumps({"label": "indices", "value": structure["indices"]})
    #       js.eval(
    #           "fetch('/log', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: "
    #           + json.dumps(payload)
    #           + "})"
    #       )
    #    except Exception as e:
    #        js.console.log(f"Failed to log indices to server: {e}")
    #    #for idx in reduced_lista:
    #    #    if idx in structure["indices"]:
    #    #        structure["indices"].remove(idx)
    #            #structure["indices"]
    #    #structure["indices"].extend(lista)
    #    #structure["indices"] = lista
    #    structure["descriptions"] = tasks.generate_descriptions()
    #    tasks.fix_fixed_tasks(structure)






def getTouchPos(canvas, touchEvent):
    rect = canvas.getBoundingClientRect()
    touch = touchEvent.touches.item(0)
    return touch.clientX - rect.left, touch.clientY - rect.top

def draw(event=None):
    for slider in sliders:
        slider.draw(event)

def mousedown(event):
    for slider in sliders:
        if event.target.id == slider.canvas.id:
            slider.on()
            slider.update_pose(event.offsetX, event.offsetY)
            slider.draw(event)
    event.preventDefault()

def touchdown(event):
    for slider in sliders:
        if event.target.id == slider.canvas.id:
            slider.on()
            x, y = getTouchPos(slider.canvas, event)
            slider.update_pose(x, y)
            slider.draw(event)
    event.preventDefault()

def move(event):
    for slider in sliders:
        if slider.active is True and event.target.id == slider.canvas.id:
            slider.update_pose(event.offsetX, event.offsetY)
            slider.draw(event)

def touchmove(event):
    for slider in sliders:
        if slider.active is True and event.target.id == slider.canvas.id:
            x, y = getTouchPos(slider.canvas, event)
            slider.update_pose(x, y)
            slider.draw(event)

def mouseup(event):
    for slider in sliders:
        slider.off()
        slider.draw(event)

draw(None)



# Attach event listeners to handle drawing
# mousedown
mousedown_proxy = pyodide.ffi.create_proxy(mousedown)
touchdown_proxy = pyodide.ffi.create_proxy(touchdown)
mouseover_proxy = pyodide.ffi.create_proxy(move)
touchover_proxy = pyodide.ffi.create_proxy(touchmove)
mouseup_proxy = pyodide.ffi.create_proxy(mouseup)
#canvas.addEventListener("dragstart",  mousedown_proxy)
#canvas.addEventListener('mousedown',  mousedown_proxy)
#canvas.addEventListener("touchstart", touchdown_proxy)
## mouseover
#mouseover_proxy = pyodide.ffi.create_proxy(move)
#touchover_proxy = pyodide.ffi.create_proxy(touchmove)
#canvas.addEventListener("mouseover", mouseover_proxy)
#canvas.addEventListener("dragmove",  mouseover_proxy)
#canvas.addEventListener("mousemove", mouseover_proxy)
#canvas.addEventListener("touchmove", touchover_proxy)
## mouseup
#mouseup_proxy = pyodide.ffi.create_proxy(mouseup)
#canvas.addEventListener("mouseup",     mouseup_proxy)
#canvas.addEventListener("mouseout",    mouseup_proxy)
#canvas.addEventListener("dragend",     mouseup_proxy)
#canvas.addEventListener("touchend",    mouseup_proxy)
#canvas.addEventListener("touchcancel", mouseup_proxy)
for slider in sliders:
    c = slider.canvas
    c.addEventListener("dragstart",  mousedown_proxy)
    c.addEventListener('mousedown',  mousedown_proxy)
    c.addEventListener("touchstart", touchdown_proxy)
    
    c.addEventListener("mouseover", mouseover_proxy)
    c.addEventListener("dragmove",  mouseover_proxy)
    c.addEventListener("mousemove", mouseover_proxy)
    c.addEventListener("touchmove", touchover_proxy)
    
    c.addEventListener("mouseup",     mouseup_proxy)
    c.addEventListener("mouseout",    mouseup_proxy)
    c.addEventListener("dragend",     mouseup_proxy)
    c.addEventListener("touchend",    mouseup_proxy)
    c.addEventListener("touchcancel", mouseup_proxy)




def watched_handler(event):
    #js.eval("video_watched = 1;")
    for s in sliders:
        s.draw(event)
watched_handler_proxy = pyodide.ffi.create_proxy(watched_handler)
video.addEventListener("ended", watched_handler_proxy)

def prev_button_handler(event):
    reload_video = int(js.eval("reload_video"))
    current_page = int(js.eval("currentPage"))
    if current_page == 6 and reload_video == 1:
        js.eval("reload_video = 0;")
        reload_video_function(structure)
    js.eval("answer_set = 1;")
    js.eval(f"video_watched = 1;")
    js.console.log("in prev_button_handler")
    maybe_show_value()

prev_button_handler_proxy = pyodide.ffi.create_proxy(prev_button_handler)
prev_btn.addEventListener("click", prev_button_handler_proxy)

def next_button_handler(event):
    js.eval("reload_video = 0;")
    reload_video_function(structure)
    question_index = int(js.eval("questionIndex"))
    if question_index in structure["answers"]:
        ans = structure["answers"][question_index]
        # Use the same all() check against expected_metrics
        if isinstance(ans, dict) and all(m in ans for m in expected_metrics):
            js.eval("answer_set = 1;")
            js.eval(f"video_watched = 1;")
        else:
            js.eval("answer_set = 0;")
            js.eval(f"video_watched = 0;")
    else:
        js.eval("answer_set = 0;")
        js.eval(f"video_watched = 0;")
    # --------------------------------
    maybe_show_value()

    structure["age"] = js.document.getElementById("age").value
    structure["country"] = js.document.getElementById("country").value
    structure["gender"] = js.document.getElementById("gender").value

    save_data(structure)

next_button_handler_proxy = pyodide.ffi.create_proxy(next_button_handler)
next_btn.addEventListener("click", next_button_handler_proxy)



async def submit_data(event, confirm=False):
    if confirm is False:
        confirmed = js.window.confirm("Are you sure you want to send your ratings and leave the survey at this point?")
    
    if confirmed:
        global structure
        structure['age'] = age.value
        structure['country'] = country.value
        structure["gender"] = js.document.getElementById('gender').value
        str_to_send = json.dumps(structure).replace('"', '\\"')

        a = 'fetch("submit", {\
                method: "POST", \
                headers: { "Content-Type": "text/plain" }, \
                body: "'
        # a = 'fetch("https://vps-fa03b8f8.vps.ovh.net:5421/submit", {\
        #         method: "POST", \
        #         headers: { "Content-Type": "text/plain" }, \
        #         body: "'
        b = '"})\
            .then(response => { \
                if (response.ok) { \
                    window.localStorage.clear(); \
                    document.documentElement.innerHTML = "<h1>Response received. Thanks!</h1>"; \
                    return response.text();  \
                } else { \
                    console.error("Error"); \
                    return Promise.reject("Error"); \
                } \
            }) \
            .then(data => console.log(data)) \
            .catch(error => console.error("Error:", error));'
        js.eval(a +  str_to_send + b)

send_button_handler_proxy = pyodide.ffi.create_proxy(submit_data)
send_btn.addEventListener("click", send_button_handler_proxy)

