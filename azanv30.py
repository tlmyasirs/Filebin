import csv
import os
import threading
from datetime import date, datetime, time, timedelta
import tkinter as tk
from PIL import Image, ImageTk, ImageFont, ImageDraw

print("loading .....")

# ====== Configuration ======
if os.name == "posix":
    FONT_DIR = "/usr/share/fonts/truetype/noto"
else:
    FONT_DIR = r"C:\Windows\Fonts"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(CURRENT_DIR, "table.csv")
BG_IMAGE1 = os.path.join(CURRENT_DIR, "background7.jpg")
BG_IMAGE2 = os.path.join(CURRENT_DIR, "backgroung_iqama.jpg")

# UI timers. A slower marquee timer greatly reduces idle CPU usage.
CLOCK_INTERVAL_MS = 1000
MARQUEE_INTERVAL_MS = 100

# Durations during which the countdown screen is shown after each prayer begins.
COUNTDOWN_MINUTES = {
    "Subahu": 30,
    "Sunrise": 20,
    "Maghrib": 10,
    "Isha": 15,
    "Zuhar": 15,
    "Asar": 15,
}

TAMIL_LABELS = {
    "Subahu": "சுபஹ்",
    "Sunrise": "உதயம்",
    "Zuhar": "லுஹர்",
    "Asar": "அஸர்",
    "Maghrib": "மஃரிப்",
    "Isha": "இஷா",
}

# ====== Data loading ======
def load_all_prayer_times(file_path):
    """Load and parse the CSV once; never parse prayer-time strings in the UI loop."""
    data = {}
    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                day = datetime.strptime(row["Date"].strip(), "%d/%m/%Y").date()
                times = {}
                for label, value in row.items():
                    if label != "Date" and value:
                        times[label] = datetime.strptime(value.strip(), "%I:%M %p").time()
                data[day] = times
            except (KeyError, TypeError, ValueError) as exc:
                print(f"Warning: skipping invalid CSV row {row!r}: {exc}")
    return data


def prerender_tamil_text(root):
    """Create the small, static Tamil images once on the Tk main thread."""
    try:
        tamil_font = ImageFont.truetype(
            os.path.join(FONT_DIR, "NotoSansTamil-Regular.ttf"), 100
        )
    except OSError:
        print("Warning: NotoSansTamil-Regular.ttf not found; using default font")
        tamil_font = ImageFont.load_default()

    images = {}
    for label, text in TAMIL_LABELS.items():
        image = Image.new("RGBA", (360, 210), (0, 0, 0, 0))
        ImageDraw.Draw(image).text((0, 0), text, font=tamil_font, fill="yellow")
        images[label] = ImageTk.PhotoImage(image, master=root)
    return images


prayer_data = load_all_prayer_times(CSV_FILE)


def get_todays_times(day=None):
    return prayer_data.get(day or date.today(), {})


def get_next_prayer(now=None):
    """Return the next prayer, including the current prayer's countdown window."""
    now = now or datetime.now()
    today = now.date()
    today_times = prayer_data.get(today, {})

    for label, prayer_time in today_times.items():
        prayer_dt = datetime.combine(today, prayer_time)
        iqamah_dt = prayer_dt + timedelta(minutes=COUNTDOWN_MINUTES.get(label, 15))
        if prayer_dt <= now < iqamah_dt or prayer_dt > now:
            return label, prayer_dt

    tomorrow = today + timedelta(days=1)
    for label, prayer_time in prayer_data.get(tomorrow, {}).items():
        return label, datetime.combine(tomorrow, prayer_time)

    return None, None


# ====== GUI setup ======
root = tk.Tk()
root.title("Prayer Display")
scr_width = root.winfo_screenwidth()
scr_height = root.winfo_screenheight()
root.geometry(f"{scr_width}x{scr_height}+0+0")
root.attributes("-fullscreen", True)
root.overrideredirect(True)

loading_canvas = tk.Canvas(root, width=scr_width, height=scr_height, bg="black", highlightthickness=0)
loading_canvas.pack(fill="both", expand=True)
loading_canvas.create_text(
    scr_width // 2,
    scr_height // 2,
    text="Muezzin is starting...",
    font=("Arial", 80),
    fill="white",
)
root.update_idletasks()


def load_backgrounds():
    """Decode and resize PIL images off the Tk thread; PhotoImage is made on the Tk thread."""
    try:
        first = Image.open(BG_IMAGE1).convert("RGB")
        second = Image.open(BG_IMAGE2).convert("RGB")
        first = first.resize((scr_width, scr_height), Image.Resampling.LANCZOS)
        second = second.resize((scr_width, scr_height), Image.Resampling.LANCZOS)
        root.after(0, lambda: setup_main_ui(first, second))
    except Exception as exc:
        root.after(0, lambda: show_load_error(exc))


def show_load_error(exc):
    loading_canvas.delete("all")
    loading_canvas.create_text(
        scr_width // 2,
        scr_height // 2,
        text=f"Unable to load display assets:\n{exc}",
        font=("Arial", 30),
        fill="white",
        justify="center",
    )


# PIL decoding can happen in a worker, but all Tk calls remain on the main thread.
threading.Thread(target=load_backgrounds, name="image-loader", daemon=True).start()


def setup_main_ui(background_image, countdown_image):
    bg_photo = ImageTk.PhotoImage(background_image, master=root)
    countdown_photo = ImageTk.PhotoImage(countdown_image, master=root)

    loading_canvas.destroy()

    main_canvas = tk.Canvas(root, width=scr_width, height=scr_height, highlightthickness=0)
    main_canvas.pack(fill="both", expand=True)
    main_canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    main_canvas.bg_photo = bg_photo

    time_font_size = int(scr_height / 4)
    next_font_size = int(scr_height / 4 + 10)

    time_text = main_canvas.create_text(
        scr_width // 2 + 30, scr_height // 4 - 100,
        text="", font=("Rubik", time_font_size, "bold"), fill="lime"
    )
    next_text = main_canvas.create_text(
        scr_width // 2 - 180, scr_height // 2 - 50,
        text="", font=("Rubik", next_font_size, "bold"), fill="yellow", anchor="w"
    )
    extra_text = main_canvas.create_text(
        scr_width // 2 - 180, scr_height * 3 // 4 - 20,
        text="", font=("Rubik", next_font_size, "bold"), fill="red", anchor="w"
    )
    waqth_text = main_canvas.create_text(
        scr_width // 2 - 280, scr_height // 2 - 80,
        text="", font=("Rubik", 50), fill="yellow", anchor="e"
    )
    iqama_text = main_canvas.create_text(
        scr_width // 2 - 280, scr_height * 3 // 4 + 30,
        text="", font=("Amiri", 80), fill="red", anchor="e"
    )

    countdown_canvas = tk.Canvas(root, width=scr_width, height=scr_height, highlightthickness=0)
    countdown_canvas.create_image(0, 0, image=countdown_photo, anchor="nw")
    countdown_canvas.bg_photo = countdown_photo
    countdown_title = countdown_canvas.create_text(
        scr_width // 2, scr_height // 6, text="", font=("Arial", 50, "bold"), fill="white"
    )
    countdown_time = countdown_canvas.create_text(
        scr_width // 2, scr_height // 3, text="", font=("Arial", 300, "bold"), fill="red"
    )
    countdown_canvas.create_text(
        scr_width // 2, scr_height * 5 // 8,
        text="Please Turn off", font=("Arial", 130), fill="white", anchor="center", width=scr_width
    )
    countdown_canvas.create_text(
        scr_width // 2, scr_height * 6 // 8,
        text="Your Mobile Phones", font=("Arial", 120), fill="white", anchor="center", width=scr_width
    )

    tamil_images = prerender_tamil_text(root)
    tamil_img_item = None
    marquee_item = None
    marquee_text = ""
    last_display = None
    last_marquee_key = None
    last_day = None
    in_countdown = False
    countdown_end = None
    countdown_label = ""
    next_prayer = get_next_prayer()

    def set_display(label, prayer_dt):
        nonlocal tamil_img_item, last_display
        iqamah_dt = prayer_dt + timedelta(minutes=COUNTDOWN_MINUTES.get(label, 15))
        display = (
            label,
            prayer_dt.strftime("%I:%M"),
            iqamah_dt.strftime("%I:%M"),
            "இகாமத்" if label != "Sunrise" else "லுஹா",
        )
        if display == last_display:
            return
        last_display = display
        if label in tamil_images:
            if tamil_img_item is None:
                tamil_img_item = main_canvas.create_image(
                    scr_width // 2 - 250, scr_height // 2 + 80,
                    anchor="e", image=tamil_images[label]
                )
            else:
                main_canvas.itemconfig(tamil_img_item, image=tamil_images[label])
        main_canvas.itemconfig(waqth_text, text=display[0])
        main_canvas.itemconfig(next_text, text=display[1])
        main_canvas.itemconfig(extra_text, text=display[2])
        main_canvas.itemconfig(iqama_text, text=display[3])

    def refresh_marquee(day, current_label):
        nonlocal marquee_item, marquee_text, last_marquee_key
        key = (day, current_label)
        if key == last_marquee_key:
            return
        last_marquee_key = key
        parts = []
        for label, prayer_time in get_todays_times(day).items():
            if label in ("Sunrise", current_label):
                continue
            clean_label = {"Subahu": "", "Maghrib": "Marib", "Asar": "Asr"}.get(label, label)
            parts.append(f"{clean_label} {prayer_time.strftime('%I:%M').lstrip('0')}")
        new_text = "   ".join(parts)
        if new_text == marquee_text:
            return
        #marquee_text = new_text
        marquee_text = "இஷா தொழுகை வழமையை விட சற்று தாமதமாக நடை பெறும்"
        if marquee_item is not None:
            main_canvas.delete(marquee_item)
        marquee_item = main_canvas.create_text(
            scr_width + 20, scr_height - 50, text=marquee_text,
            font=("Arial", 90, "bold"), fill="white", anchor="e"
        )

    def update_countdown(seconds, label):
        minutes, secs = divmod(max(0, seconds), 60)
        countdown_canvas.itemconfig(countdown_title, text=f"{label.upper()} - COUNTDOWN")
        countdown_canvas.itemconfig(countdown_time, text=f"{minutes:02}:{secs:02}")

    def update_clock():
        nonlocal next_prayer, in_countdown, countdown_end, countdown_label, last_day, last_marquee_key
        now = datetime.now()
        current_day = now.date()
        main_canvas.itemconfig(time_text, text=now.strftime("%I:%M:%S"))

        if current_day != last_day:
            last_day = current_day
            next_prayer = get_next_prayer(now)
            last_marquee_key = None

        if in_countdown:
            remaining = int((countdown_end - now).total_seconds())
            if remaining > 0:
                update_countdown(remaining, countdown_label)
                root.after(CLOCK_INTERVAL_MS, update_clock)
                return
            in_countdown = False
            countdown_canvas.pack_forget()
            main_canvas.pack(fill="both", expand=True)
            next_prayer = get_next_prayer(now)

        if not next_prayer or not next_prayer[0]:
            next_prayer = get_next_prayer(now)

        label, prayer_dt = next_prayer
        iqamah_dt = prayer_dt + timedelta(minutes=COUNTDOWN_MINUTES.get(label, 15))
        if prayer_dt <= now < iqamah_dt:
            in_countdown = True
            countdown_label = label
            countdown_end = iqamah_dt
            main_canvas.pack_forget()
            countdown_canvas.pack(fill="both", expand=True)
            update_countdown(int((iqamah_dt - now).total_seconds()), label)
        elif now >= iqamah_dt:
            next_prayer = get_next_prayer(now)
            if next_prayer[0]:
                label, prayer_dt = next_prayer

        if not in_countdown:
            set_display(label, prayer_dt)
            refresh_marquee(current_day, label)
        root.after(CLOCK_INTERVAL_MS, update_clock)

    def scroll_marquee():
        if marquee_item is not None and not in_countdown:
            main_canvas.move(marquee_item, -5, 0)
            bounds = main_canvas.bbox(marquee_item)
            if bounds and bounds[2] < 0:
                width = bounds[2] - bounds[0]
                main_canvas.move(marquee_item, scr_width + width, 0)
        root.after(MARQUEE_INTERVAL_MS, scroll_marquee)

    print("Starting the application...")
    update_clock()
    scroll_marquee()


root.mainloop()
