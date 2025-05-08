import csv
import os
from datetime import datetime, timedelta
import tkinter as tk
from PIL import Image, ImageTk
import time

print('loading .....')
# --- Load today's prayer times ---
def load_prayer_times(file_path):
    print(file_path)
    today = datetime.now().strftime('%d/%m/%Y')
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Date'] == today:
                return {k: row[k] for k in row if k != 'Date'}
    return {}

file='/home/pi/azan/table.csv'
times = load_prayer_times(file)

if not times:
    print("Today's data not found in the CSV!")
    exit()

print('table read')

time_objs = [(label, datetime.strptime(times[label], '%I:%M %p').time()) for label in times]

# --- Get next upcoming prayer times ---
def get_next_times(prayer_times):
    now_dt = datetime.now()
    upcoming = []

    # Check for any upcoming times today
    for label, t in prayer_times:
        prayer_dt = datetime.combine(now_dt.date(), t)
        if prayer_dt > now_dt:
            upcoming.append((label, prayer_dt))

    # If no upcoming times left for today, try reloading tomorrow's times
    if len(upcoming) < 1:
        tomorrow = now_dt + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%d/%m/%Y')

        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == tomorrow_str:
                    next_day_times = [(label, datetime.strptime(row[label], '%I:%M %p').time())
                                      for label in row if label != 'Date']
                    upcoming = [
                        (label, datetime.combine(tomorrow.date(), t))
                        for label, t in next_day_times
                    ]
                    break

    return upcoming[:1]


# --- GUI Setup ---
root = tk.Tk()
root.title("Prayer Display")
scr_width = root.winfo_screenwidth()
scr_height = root.winfo_screenheight()

root.geometry(f"{scr_width}x{scr_height}")
# move window to right a bit
#root.geometry(f"+{scr_width // 8}+{scr_height // 50}")
#root.overrideredirect(True)
root.attributes('-fullscreen', True)

# Load background images
bg_image = Image.open("/home/pi/azan/background3.jpg")
bg_photo = ImageTk.PhotoImage(bg_image.resize((scr_width, scr_height)))
bg_image1 = Image.open("/home/pi/azan/background5.jpg")
bg_photo1 = ImageTk.PhotoImage(bg_image1.resize((scr_width, scr_height)))

# Main canvas
main_canvas = tk.Canvas(root, width=scr_width, height=scr_height)
main_canvas.pack(fill="both", expand=True)
main_canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Display elements
time_text = main_canvas.create_text(
    scr_width // 2, scr_height // 6, text="", font=("Rubik", 220, "bold"), fill="lime"
)
next_text = main_canvas.create_text(
    scr_width // 2, scr_height // 2.5, text="", font=("Rubik", 230, "bold"), fill="yellow"
)
extra_text = main_canvas.create_text(
    scr_width // 2, scr_height * 2 // 3, text="", font=("Rubik", 230, "bold"), fill="red"
)
waqth_text = main_canvas.create_text(
    20, scr_height // 2.5, text="", font=("Rubik", 80), fill="yellow", anchor="w"
)

# Countdown canvas
countdown_canvas = tk.Canvas(root, width=scr_width, height=scr_height)
countdown_canvas.create_image(0, 0, image=bg_photo1, anchor="nw")

# --- Countdown screen ---
def countdown_screen(secs, next_prayer_label):
    print("in countdown")
    
    print(f'insie cnt{secs}')
    if secs <= 0:
        print("countdown finished")
        # Exit countdown and return to the main screen
        countdown_canvas.pack_forget()
        main_canvas.pack(fill="both", expand=True)
        time.sleep(1)  # Sleep for a second to show the last countdown
        update()  # Refresh for the next prayer
        return
    print("countdown...")
    main_canvas.pack_forget()
    countdown_canvas.pack(fill="both", expand=True)
    # Clear the countdown canvas
    countdown_canvas.delete("all")
    countdown_canvas.create_image(0, 0, image=bg_photo1, anchor="nw")
    # make countdown canvas visible
    countdown_canvas.pack(fill="both", expand=True)

    # Add countdown text to the countdown canvas
    countdown_canvas.create_text(
        scr_width // 2, scr_height // 6,
        text=f"{next_prayer_label.upper()} - COUNTDOWN",
        font=("Arial", 50, "bold"),
        fill="white"
    )

    # Format the countdown as mm:ss
    mins, secs = divmod(int(secs), 60)
    countdown_canvas.create_text(
        scr_width // 2, scr_height // 3,
        text=f"{mins:02}:{secs:02}",
        font=("Arial", 300, "bold"),
        fill="red"
    )

    countdown_canvas.create_text(
        scr_width // 2, scr_height * 5 // 8,
        text="Please Turn off",
        font=("Arial", 130),
        fill="white",
	anchor="center",
	width=scr_width
    )

    countdown_canvas.create_text(
        scr_width // 2, scr_height * 7 // 8,
        text="Your Mobile Phones",
        font=("Arial", 120),
        fill="white",
        anchor="center",
        width=scr_width
    )
    # Schedule the next countdown update
    #root.after(1000, lambda: countdown_screen(secs - 1, next_prayer_label))


# --- Update loop ---
def update():
    now_dt = datetime.now()
    main_canvas.itemconfig(time_text, text=now_dt.strftime('%I:%M:%S '))#%p'))

    # get global variable next_2
    global next_2
    # Check if next_2 is empty or not
    if next_2:
        #print('oooooo')
        #print(next_2)
        label, next_time = next_2[0]

        label_minutes = {
                "Subahu": 30,
                "Sunrise": 20,
                "Maghrib": 10,
            }

        duration = label_minutes.get(label, 15)
        iqamah_time = next_time + timedelta(minutes=duration)

        time_to_next_prayer = (iqamah_time - now_dt).total_seconds()
        #print(now_dt, next_time, iqamah_time)
        if next_time < now_dt < iqamah_time:
            print('countdown cond met')
            countdown_screen(int(time_to_next_prayer), label)

        if now_dt > iqamah_time:
            # Update the next prayer and iqamah time on the main canvas
            next_2 = get_next_times(time_objs)
            #main_canvas.pack(fill="both", expand=True)

        main_canvas.itemconfig(waqth_text, text=label)
        main_canvas.itemconfig(next_text, text=f"{next_time.strftime('%I:%M')}")
        main_canvas.itemconfig(extra_text, text=f"{iqamah_time.strftime('%I:%M')}")

    root.after(1000, update)  # Schedule the next update


# --- Start ---
# gloab variable to store next_2
global next_2
next_2 = get_next_times(time_objs)
label, next_time = next_2[0]
print('vars inited, starting app')
update()
root.mainloop()

