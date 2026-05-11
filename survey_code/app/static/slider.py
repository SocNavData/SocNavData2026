import js
import math

MIN_ANSWERS = 50

def project_point_to_segment(x1, y1, x2, y2, x, y):
    # Calculate the square of the length of the segment
    segment_length_squared = (x2 - x1) ** 2 + (y2 - y1) ** 2
    # If the segment length is zero, return the distance between the point and the single endpoint
    if segment_length_squared == 0:
        return math.sqrt((x - x1) ** 2 + (y - y1) ** 2)
    # Calculate the projection of point (x, y) onto the line defined by the segment
    t = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / segment_length_squared
    # Clamp t to the range [0, 1] to ensure the projection falls on the segment
    t = max(0, min(1, t))
    # Find the coordinates of the projection point on the segment
    prj_x = x1 + t * (x2 - x1)
    prj_y = y1 + t * (y2 - y1)
    return prj_x, prj_y, t


def distance_point_to_segment(x1, y1, x2, y2, x, y):
    prj_x, prj_y, _ = project_point_to_segment(x1, y1, x2, y2, x, y)
    # Calculate the distance between the point and the projection
    distance = math.sqrt((x - prj_x) ** 2 + (y - prj_y) ** 2)    
    return distance


class Slider(object):
    def __init__(self, canvas, structure, metric_name, expected_metrics):
        super().__init__()
        self.value = None
        self.canvas = canvas
        self.metric_name = metric_name
        self.expected_metrics = expected_metrics
        self.radius = 14
        self.shown_message = False
        self.ctx = self.canvas.getContext('2d')
        self.structure = structure
        self.off()

    def draw(self, event=None):
        canvas = self.canvas
        radius = 16 # Slightly larger, more tactile thumb
        
        # Generous margin so text breathes
        margin = 55
        x_start = margin
        x_end = canvas.width - margin
        
        ctx = self.ctx
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        video_watched = int(js.eval("video_watched"))
        if video_watched != 1:
            return

        slider_offset = 15

        # ---------------------------------------------------
        # 1. DRAW MODERN TRACK (Thick, rounded, light gray)
        # ---------------------------------------------------
        ctx.lineCap = "round"
        ctx.lineWidth = 9  # Thicker track
        ctx.strokeStyle = "#e2e8f0" # Modern light slate-gray
        
        ctx.beginPath()
        ctx.moveTo(x_start, canvas.height/2+slider_offset)
        ctx.lineTo(x_end, canvas.height/2+slider_offset)
        ctx.stroke()

        # Optional: Draw a center marker (subtle dot instead of a harsh line)
        ctx.beginPath()
        ctx.arc((x_start+x_end)//2, canvas.height/2+slider_offset, 4, 0, 6.28)
        ctx.fillStyle = "#cbd5e1"
        ctx.fill()

        # ---------------------------------------------------
        # 2. DRAW THUMB (With drop shadow and border)
        # ---------------------------------------------------
        if self.value is not None:
            ctx.beginPath()
            x = x_start + self.value*(x_end-x_start)
            y = canvas.height//2+slider_offset
            ctx.arc(int(x), int(y), int(radius), 0, 6.28)
            
            # Dynamic Red-to-Green Color
            r = str(hex(int((1-self.value)*240))).split('x')[-1].zfill(2)
            g = str(hex(int((  self.value)*240))).split('x')[-1].zfill(2)
            b = "10" # Adding a tiny bit of blue softens the neon colors
            
            # Add a nice drop shadow so it "pops" off the screen
            ctx.shadowColor = "rgba(0, 0, 0, 0.25)"
            ctx.shadowBlur = 6
            ctx.shadowOffsetY = 2
            
            ctx.fillStyle = "#"+r+g+b+"FF"
            ctx.fill()
            
            # Turn off shadow for the stroke
            ctx.shadowColor = "transparent"
            
            # Add a clean white border around the thumb
            ctx.lineWidth = 2
            ctx.strokeStyle = "#ffffff"
            ctx.stroke()

        # ---------------------------------------------------
        # 3. DRAW MODERN TYPOGRAPHY (Sans-serif, muted colors)
        # ---------------------------------------------------
        # Using a modern font stack
        ctx.font = "14px 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
        ctx.fillStyle = "#64748b" # Muted slate text so it isn't aggressively black
        ctx.textBaseline = "top"
        ctx.textAlign = "center"

        # Left label
        ctx.fillText("Extremely", x_start, 0)
        ctx.fillText("bad", x_start, 20)
        
        # Center label
        ctx.fillText("Fair", (x_start+x_end)//2, 20)
        
        # Right label
        ctx.fillText("Extremely", x_end, 0)
        ctx.fillText("good", x_end, 20)


    def update_pose(self, x, y):
        video_watched = int(js.eval("video_watched"))
        # if video_watched != 1:
        #     js.window.confirm("Please, watch the video before providing a rating.")
        #     return

        radius = self.radius
        x_start = int(2*radius)
        x_end = int(self.canvas.width - 2*radius)

        x1 = x_start
        y1 = radius
        x2 = x_end
        y2 = radius
        _, _, t = project_point_to_segment(x1, y1, x2, y2, x, y)
        self.set_value(t)

    def set_value(self, v):
        question_index = int(js.eval("questionIndex"))
        self.value = v

        if question_index not in self.structure["answers"] or not isinstance(self.structure["answers"][question_index], dict):
            self.structure["answers"][question_index] = {}
        self.structure["answers"][question_index][self.metric_name] = self.value
        ans = self.structure["answers"][question_index]
        if all(metric in ans for metric in self.expected_metrics):
            js.eval("answer_set = 1;")
        else:
            js.eval("answer_set = 0;")
        if question_index == MIN_ANSWERS - 1 and self.shown_message == False:
            js.alert(f"Thank you for submitting your {MIN_ANSWERS} ratings. Feel free to rate more trajectories. When you are done, please click on \"send\".")
            self.shown_message = True
        #js.eval("answer_set = 1;")

    def on(self):
        self.active = True

    def off(self):
        self.active = False
