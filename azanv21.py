import csv
import os
import threading
from datetime import datetime, timedelta
import tkinter as tk
from PIL import Image, ImageTk, ImageFont, ImageDraw

print('loading .....')
current_prayer = None
# ====== Configuration Constants ======
if os.name == 'posix':
    FONT_DIR = "/usr/share/fonts/truetype/noto/"
else:
    FONT_DIR = r"C:\Windows\Fonts"
#get current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(CURRENT_DIR, "table.csv")
BG_IMAGE1 = os.path.join(CURRENT_DIR, "background7.jpg")
BG_IMAGE2 = os.path.join(CURRENT_DIR, "backgroung_iqama.jpg")


# ====== Precomputed Values ======
# Preload all prayer times
def load_all_prayer_times(file_path):
    data = {}
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['Date']] = {k: row[k] for k in row if k != 'Date'}
    return data

# Pre-render Tamil text images99
def prerender_tamil_text():
    lookup_dict = {
        "Subahu": "சுபஹ்",
        "Sunrise": "உதயம்",
        "Zuhar": "லுஹர்",
        "Asar": "அஸர்",
        "Maghrib": "மஃரிப்",
        "Isha": "இஷா"
    }
    # Use arial.ttf for Windows compatibility (Note: Tamil rendering might be imperfect with standard Arial)
    try:
        tamil_font = ImageFont.truetype(os.path.join(FONT_DIR, "NotoSansTamil-Regular.ttf"), 100)
    except OSError:
        # Fallback to default if arial.ttf is not found (e.g. on Linux/different OS)
        print("Warning: NotoSansTamil-Regular.ttf not found, using load_default()")
        tamil_font = ImageFont.load_default()

    images = {}
    
    for label, text in lookup_dict.items():
        img = Image.new("RGBA", (360, 210), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), text, font=tamil_font, fill="yellow")
        tk_img = ImageTk.PhotoImage(img)
        images[label] = tk_img
    return images

# Load data and prerender images
prayer_data = load_all_prayer_times(CSV_FILE)


# ====== Prayer Time Functions ======
def get_todays_times():
    today = datetime.now().strftime('%d/%m/%Y')
    return prayer_data.get(today, {})

def get_next_prayer():
    now_dt = datetime.now()
    today = now_dt.strftime('%d/%m/%Y')
    tomorrow = (now_dt + timedelta(days=1)).strftime('%d/%m/%Y')
    
    # Find next prayer today
    if today in prayer_data:
        times = prayer_data[today]
        for label, time_str in times.items():
            prayer_time = datetime.strptime(time_str, '%I:%M %p').time()
            prayer_dt = datetime.combine(now_dt.date(), prayer_time)
            if prayer_dt > now_dt:
                return label, prayer_dt

    # Find first prayer tomorrow
    if tomorrow in prayer_data:
        times = prayer_data[tomorrow]
        for label, time_str in times.items():
            prayer_time = datetime.strptime(time_str, '%I:%M %p').time()
            prayer_dt = datetime.combine((now_dt + timedelta(days=1)).date(), prayer_time)
            return label, prayer_dt

    return None, None

# ====== GUI Setup ======
root = tk.Tk()
root.title("Prayer Display")
scr_width = root.winfo_screenwidth()
scr_height = root.winfo_screenheight()
root.geometry(f"{scr_width}x{scr_height}")
root.attributes('-fullscreen', True)

# Create loading screen
loading_canvas = tk.Canvas(root, width=scr_width, height=scr_height, bg='black')
loading_canvas.pack(fill="both", expand=True)
loading_text = loading_canvas.create_text(
    scr_width // 2, scr_height // 2, 
    text="Muezzin is starting...", 
    font=("Arial", 80), 
    fill="white"
)
root.update()  # Force immediate display of loading screen

# Function to load images in background
def load_images():
    # Load background images
    bg_image = Image.open(BG_IMAGE1)
    bg_photo = ImageTk.PhotoImage(bg_image.resize((scr_width, scr_height)))
    
    bg_image1 = Image.open(BG_IMAGE2)
    bg_photo1 = ImageTk.PhotoImage(bg_image1.resize((scr_width, scr_height)))
    
    # Pass to main thread
    root.after(0, lambda: setup_main_ui(bg_photo, bg_photo1))

# Start image loading in separate thread
threading.Thread(target=load_images, daemon=True).start()

# ====== Main UI Setup ======
def setup_main_ui(bg_photo, bg_photo1):
    # Remove loading screen
    loading_canvas.pack_forget()
    
    # Main canvas
    main_canvas = tk.Canvas(root, width=scr_width, height=scr_height)
    main_canvas.pack(fill="both", expand=True)
    main_canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    main_canvas.bg_photo = bg_photo  # Keep reference

    time_font_size = int(scr_height / 4) 
    next_fornt_size = int(scr_height / 4 + 10)
    # Display elements
    time_text = main_canvas.create_text(
        scr_width // 2 + 30, scr_height // 4 - 100, text="", font=("Rubik", time_font_size, "bold"), fill="lime"
    )
    next_text = main_canvas.create_text(
        scr_width // 2 - 180, scr_height // 2 -50, text="", font=("Rubik", next_fornt_size, "bold"), fill="yellow", anchor="w"
    )
    extra_text = main_canvas.create_text(
        scr_width // 2 - 180, scr_height * 3 // 4 - 20, text="", font=("Rubik", next_fornt_size, "bold"), fill="red", anchor="w"
    )
    waqth_text1 = main_canvas.create_text(
        scr_width // 2 - 280, scr_height // 2 -80, text="", font=("Rubic", 50), fill="yellow", anchor="e"
    )
    iqama_txt = main_canvas.create_text(
        scr_width // 2 - 280, scr_height * 3 // 4 +30, text="", font=("Amiri", 80), fill="red", anchor="e"
    )

    # Countdown canvas
    countdown_canvas = tk.Canvas(root, width=scr_width, height=scr_height)
    countdown_canvas.create_image(0, 0, image=bg_photo1, anchor="nw")
    countdown_canvas.bg_photo = bg_photo1  # Keep reference

    # Create static countdown elements
    countdown_title = countdown_canvas.create_text(
        scr_width // 2, scr_height // 6,
        text="", font=("Arial", 50, "bold"), fill="white"
    )
    countdown_time = countdown_canvas.create_text(
        scr_width // 2, scr_height // 3,
        text="", font=("Arial", 300, "bold"), fill="red"
    )
    countdown_line1 = countdown_canvas.create_text(
        scr_width // 2, scr_height * 5 // 8,
        text="Please Turn off", font=("Arial", 130), fill="white", anchor="center", width=scr_width
    )
    countdown_line2 = countdown_canvas.create_text(
        scr_width // 2, scr_height * 6 // 8,
        text="Your Mobile Phones", font=("Arial", 120), fill="white", anchor="center", width=scr_width
    )

    # ====== Prayer Time Logic ======
    label_minutes = {
        "Subahu": 30,
        "Sunrise": 20,
        "Maghrib": 10,
    }

    # ====== State Management ======
    class AppState:
        def __init__(self):
            self.in_countdown = False
            self.current_countdown_label = ""
            self.current_countdown_end = None
            self.next_prayer = get_next_prayer()
    
    state = AppState()

    # ====== Countdown Functions ======
    def update_countdown(seconds, label):
        mins, secs = divmod(seconds, 60)
        countdown_canvas.itemconfig(countdown_title, text=f"{label.upper()} - COUNTDOWN")
        countdown_canvas.itemconfig(countdown_time, text=f"{mins:02}:{secs:02}")
        
        # If countdown reaches 0, return to main screen
        if seconds <= 0:
            state.in_countdown = False
            state.current_countdown_label = ""
            state.current_countdown_end = None
            countdown_canvas.pack_forget()
            main_canvas.pack(fill="both", expand=True)
            # Refresh next prayer after countdown completes
            state.next_prayer = get_next_prayer()
            return False  # Stop countdown
        
        return True  # Continue countdown

    # ====== Main Update Loop ======
    # Add this line at the start of setup_main_ui to track the image item
    main_canvas.tamil_img_item = None

    def update():
        global current_prayer
        now_dt = datetime.now()
        
        # Always update the clock
        main_canvas.itemconfig(time_text, text=now_dt.strftime('%I:%M:%S '))
        
        # Handle countdown state
        if state.in_countdown:
            # Calculate remaining time
            remaining = int((state.current_countdown_end - now_dt).total_seconds())
            if update_countdown(remaining, state.current_countdown_label):
                # Continue countdown if not finished
                root.after(1000, update)
                return
            # If countdown finished, we proceed to update main screen
        
        # Get next prayer if not available
        if not state.next_prayer or not state.next_prayer[0]:
            state.next_prayer = get_next_prayer()
        
        if state.next_prayer[0]:
            label, prayer_time = state.next_prayer
            current_prayer = label
            duration = label_minutes.get(label, 15)
            iqamah_time = prayer_time + timedelta(minutes=duration)
            
            # Check if we should start countdown
            if prayer_time <= now_dt < iqamah_time and not state.in_countdown:
                # Start countdown
                state.in_countdown = True
                state.current_countdown_label = label
                state.current_countdown_end = iqamah_time
                countdown_canvas.pack(fill="both", expand=True)
                main_canvas.pack_forget()
                remaining = int((iqamah_time - now_dt).total_seconds())
                update_countdown(remaining, label)
                root.after(1000, update)
                return
            
            # Update to next prayer if current has passed
            if now_dt >= iqamah_time:
                state.next_prayer = get_next_prayer()
                if state.next_prayer[0]:
                    label, prayer_time = state.next_prayer
            
            # Update display
            if state.next_prayer[0]:
                # Update Tamil image
                if label in tamil_images:
                    # Remove previous Tamil image if exists
                    if main_canvas.tamil_img_item is not None:
                        main_canvas.delete(main_canvas.tamil_img_item)
                    main_canvas.tk_img = tamil_images[label]  # Keep reference
                    main_canvas.tamil_img_item = main_canvas.create_image(
                        scr_width // 2 - 250, scr_height // 2 + 80,
                        anchor="e", image=tamil_images[label]
                    )
                
                # Update text elements
                main_canvas.itemconfig(waqth_text1, text=label)
                main_canvas.itemconfig(next_text, text=prayer_time.strftime('%I:%M'))
                main_canvas.itemconfig(extra_text, text=iqamah_time.strftime('%I:%M'))
                main_canvas.itemconfig(iqama_txt, text="இகாமத்" if label != "Sunrise" else "லுஹா")
        
        root.after(1000, update)

    # ====== Marquee Functionality ======
    marquee_text_item = None
    marquee_msg = ""
    

    def update_marquee_text():
        global current_prayer
        nonlocal marquee_msg, marquee_text_item
        scroll_data = get_todays_times().copy()
        # pop Sunrise from data
        a = "Sunrise"

        scroll_data.pop(a, None)
        scroll_data.pop(current_prayer,None)
        #print(data)
        # data into string without {,}, and ' AM ,PM, Sunrise time
        new_msg = str(scroll_data).replace("{", "").replace("}", "").replace("'", "").replace("AM", "").replace("PM", "").replace(" ,", "").replace(": ", " ").replace("Subahu", "").replace("Maghrib", "Marib").replace("Asar", "Asr")
                
        # Only update if changed
        if new_msg != marquee_msg:
            marquee_msg = new_msg
            if marquee_text_item:
                main_canvas.delete(marquee_text_item)
            
            # Create new text item centered at the bottom
            marquee_text_item = main_canvas.create_text(
                scr_width // 2, scr_height - 50,
                text=marquee_msg,
                font=("Arial", 90, "bold"),
                fill="white",
                anchor="center"
            )

    # Initialize marquee
    # run the marquee 
    update_marquee_text()
    # scroll the marquee
    def scroll_marquee():
        nonlocal marquee_text_item
        if marquee_text_item:
            x1, y1, x2, y2 = main_canvas.bbox(marquee_text_item)
            main_canvas.move(marquee_text_item, -5, 0)
            # if text end is at right side
            width = x2 - x1
            if x2 < 1100:
                # Reset to right side, maintaining same Y coordinate
                
                main_canvas.coords(marquee_text_item, width -300, scr_height - 50)
        #root.after(50, scroll_marquee)
    
    #scroll_marquee()
    
    
    # Hook into main update to check for day changes periodically
    # We can just add a check in the main update loop to refresh text if day changes
    original_update = update
    def update_with_marquee_check():
        # Check if message needs updating (essentially on day change)
        # We can do this less frequently or just every second as it's a dict lookup
        update_marquee_text()
        original_update()
    
    # Overwrite the update reference so it runs our wrapper
    update = update_with_marquee_check


    # ====== Initialization ======
    print('Starting the application...')
    update()

tamil_images = prerender_tamil_text()

# Start main loop
root.mainloop()
