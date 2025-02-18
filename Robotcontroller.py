import serial
import tkinter as tk
from tkinter import messagebox, filedialog
import time
import json
import re


# Open serial connection to Arduino
arduino = serial.Serial('COM3', 115200, timeout=0.1)  # Replace 'COM3' with your actual port

# Function to send command to Arduino
def send_command(command):
    arduino.write((command + '\n').encode())
    time.sleep(0.05)
    response = ''
    while arduino.in_waiting > 0:
        response += arduino.readline().decode().strip()
    return response

# Function to get current position from Arduino
def get_position():
    response = send_command("POSITION")
    current_positions.set(response)

# Function to set speed and acceleration for a specific axis
def set_speed_accel(axis):
    speed = entry_speed[axis].get()
    accel = entry_accel[axis].get()

    if not speed or not accel:
        messagebox.showerror("Input Error", f"Please provide both speed and acceleration for {axis}.")
        return

    try:
        speed = int(speed)
        accel = int(accel)
        if speed < 0 or accel < 0:
            messagebox.showerror("Input Error", "Speed and Acceleration must be non-negative values.")
            return
        response = send_command(f"SET {axis} {speed} {accel}")
        status_message.set(response)
    except ValueError:
        messagebox.showerror("Input Error", "Speed and Acceleration must be integers.")

# Function to move motors to absolute position
def move_abs():
    x_pos = entry_x_pos.get()
    y_pos = entry_y_pos.get()
    z_pos = entry_z_pos.get()

    if not x_pos or not y_pos or not z_pos:
        messagebox.showerror("Input Error", "Please provide positions for X, Y, and Z.")
        return

    try:
        x_pos = int(x_pos)
        y_pos = int(y_pos)
        z_pos = int(z_pos)
        response = send_command(f"MOVEABS {x_pos} {y_pos} {z_pos}")
        status_message.set(response)
    except ValueError:
        messagebox.showerror("Input Error", "Positions must be integers.")

# Function to stop motors
def stop_motors():
    response = send_command("STOP")
    status_message.set(response)

# # Function to zero all axes
# def zero_all_axes(self):
   

# Variables to store key states
key_states = {'Up': False, 'Down': False, 'Left': False, 'Right': False, 'w': False, 's': False}

# Function to handle key press events
def on_key_press(event):
    if event.keysym in key_states and not key_states[event.keysym]:
        key_states[event.keysym] = True
        update_motors()

# Function to handle key release events
def on_key_release(event):
    if event.keysym in key_states:
        key_states[event.keysym] = False

# Function to update motors based on key states
def update_motors():
    x_move = 0
    y_move = 0
    z_move = 0
    if key_states['Up']:
        y_move -= 300
    if key_states['Down']:
        y_move += 300
    if key_states['Left']:
        x_move -= 300
    if key_states['Right']:
        x_move += 300
    if key_states['w']:
        z_move -= 300
    if key_states['s']:
        z_move += 300

    if x_move != 0 or y_move != 0 or z_move != 0:
        response = send_command(f"MOVEREL {x_move} {y_move} {z_move}")
        status_message.set(response)
        # Continue updating while keys are pressed
        root.after(50, update_motors)

# Variables to store sequence of positions
sequence = []

# Function to add position to sequence
def add_position_to_sequence():
    x_pos = entry_x_seq.get()
    y_pos = entry_y_seq.get()
    z_pos = entry_z_seq.get()
    duration = entry_duration.get()

    if not x_pos or not y_pos or not z_pos or not duration:
        messagebox.showerror("Input Error", "Please provide X, Y, Z positions and duration.")
        return

    try:
        x_pos = int(x_pos)
        y_pos = int(y_pos)
        z_pos = int(z_pos)
        duration = float(duration)
        if len(sequence) >= 10:
            messagebox.showerror("Sequence Full", "Cannot add more than 10 positions.")
            return
        sequence.append({
            "X": x_pos,
            "Y": y_pos,
            "Z": z_pos,
            "Duration": duration
        })
        update_sequence_display()
        entry_x_seq.delete(0, tk.END)
        entry_y_seq.delete(0, tk.END)
        entry_z_seq.delete(0, tk.END)
        entry_duration.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Input Error", "Positions must be integers and duration must be a number.")

def add_current_position_to_sequence():
    try:
        pos_text = current_positions.get()
        
        # Use regex to extract X, Y, Z values
        match = re.match(r'X:(-?\d+)Y:(-?\d+)Z:(-?\d+)', pos_text)
        if not match:
            raise ValueError("Position string format is incorrect.")

        x_pos, y_pos, z_pos = map(int, match.groups())
        duration=(entry_duration.get())  # Default duration in seconds
        duration = float(duration)

        if len(sequence) >= 10:
            messagebox.showerror("Sequence Full", "Cannot add more than 10 positions.")
            return

        sequence.append({
            "X": x_pos,
            "Y": y_pos,
            "Z": z_pos,
            "Duration": duration
        })
        update_sequence_display()
        
    except (ValueError, IndexError) as e:
        print(f"Error parsing position: {e}")  # Debug statement
        messagebox.showerror("Input Error", "Invalid current position.")

# Function to update sequence display
def update_sequence_display():
    sequence_display.delete(0, tk.END)
    for idx, pos in enumerate(sequence):
        sequence_display.insert(tk.END, f"{idx+1}: X={pos['X']} Y={pos['Y']} Z={pos['Z']} Duration={pos['Duration']}s")

# Function to save sequence to a file
def save_sequence():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files","*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            json.dump(sequence, file)
        status_message.set("Sequence saved.")

# Function to load sequence from a file
def load_sequence():
    global sequence
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files","*.txt")])
    if file_path:
        try:
            with open(file_path, "r") as file:
                sequence = json.load(file)
            update_sequence_display()
            status_message.set("Sequence loaded.")
        except FileNotFoundError:
            messagebox.showerror("Load Sequence", "File not found.")
        except json.JSONDecodeError:
            messagebox.showerror("Load Sequence", "Error decoding the file.")

# Function to run the sequence
def run_sequence():
    for pos in sequence:
        response = send_command(f"MOVEABS {pos['X']} {pos['Y']} {pos['Z']}")
        status_message.set(response)
        time.sleep(pos['Duration'])
    status_message.set("Sequence completed.")

# Function to clear the sequence
def clear_sequence():
    global sequence
    sequence = []
    update_sequence_display()

# Function to continuously update positions
def continuous_update():
    get_position()
    root.after(500, continuous_update)

# Tkinter GUI Application Class
class StepperControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stepper Motor Control")

        # Set up the GUI elements
        self.create_widgets()

        # Bind keyboard events
        self.root.bind('<KeyPress>', on_key_press)
        self.root.bind('<KeyRelease>', on_key_release)

        # Start continuous update of position
        continuous_update()

    def create_widgets(self):
        global entry_speed, entry_accel, entry_x_pos, entry_y_pos, entry_z_pos, current_positions, status_message
        global entry_x_seq, entry_y_seq, entry_z_seq, entry_duration, sequence_display

        entry_speed = {}
        entry_accel = {}

        # Define default speed and acceleration per axis
        default_values = {
            'X': {'speed': '700', 'accel': '400'},
            'Y': {'speed': '600', 'accel': '300'},
            'Z': {'speed': '500', 'accel': '200'}
        }

        # Speed and Acceleration controls for each axis
        for i, axis in enumerate(['X', 'Y', 'Z']):
            tk.Label(self.root, text=f"{axis} Speed:").grid(row=i*2, column=0, padx=5, pady=5, sticky='e')
            entry_speed[axis] = tk.Entry(self.root)
            entry_speed[axis].insert(0, default_values[axis]['speed'])
            entry_speed[axis].grid(row=i*2, column=1, padx=5, pady=5)

            tk.Label(self.root, text=f"{axis} Acceleration:").grid(row=i*2+1, column=0, padx=5, pady=5, sticky='e')
            entry_accel[axis] = tk.Entry(self.root)
            entry_accel[axis].insert(0, default_values[axis]['accel'])
            entry_accel[axis].grid(row=i*2+1, column=1, padx=5, pady=5)

            tk.Button(self.root, text=f"Set {axis}", command=lambda a=axis: set_speed_accel(a)).grid(row=i*2, column=2, rowspan=2, padx=5, pady=5)
        # Positions for Absolute Movement
        tk.Label(self.root, text="X Position (Abs):").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        entry_x_pos = tk.Entry(self.root)
        entry_x_pos.insert(0, "0")  # Default 

        entry_x_pos.grid(row=6, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Y Position (Abs):").grid(row=7, column=0, padx=5, pady=5, sticky='e')
        entry_y_pos = tk.Entry(self.root)
        entry_y_pos.insert(0, "0")  # Default 

        entry_y_pos.grid(row=7, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Z Position (Abs):").grid(row=8, column=0, padx=5, pady=5, sticky='e')
        entry_z_pos = tk.Entry(self.root)
        entry_z_pos.grid(row=8, column=1, padx=5, pady=5)
        entry_z_pos.insert(0, "0")  # Default 

        # Buttons for Commands
        tk.Button(self.root, text="Move Absolute", command=move_abs).grid(row=9, column=0, columnspan=2, padx=5, pady=5)
        tk.Button(self.root, text="Stop Motors", command=stop_motors).grid(row=9, column=2, padx=5, pady=5)

        # tk.Button(self.root, text="Zero All Axes", command=zero_all_axes).grid(row=10, column=0, columnspan=2, padx=5, pady=5)

        # Current Position display
        tk.Label(self.root, text="Current Positions:").grid(row=11, column=0, padx=5, pady=5, sticky='e')
        current_positions = tk.StringVar()
        tk.Label(self.root, textvariable=current_positions).grid(row=11, column=1, columnspan=2, padx=5, pady=5)

        # Status Message
        status_message = tk.StringVar()
        tk.Label(self.root, textvariable=status_message, fg="blue").grid(row=12, column=0, columnspan=3, padx=5, pady=5)

        # Sequence Controls
        tk.Label(self.root, text="Sequence Control").grid(row=13, column=0, columnspan=3, padx=5, pady=5)

        tk.Label(self.root, text="X:").grid(row=14, column=0, padx=5, pady=5, sticky='e')
        entry_x_seq = tk.Entry(self.root)
        entry_x_seq.grid(row=14, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Y:").grid(row=15, column=0, padx=5, pady=5, sticky='e')
        entry_y_seq = tk.Entry(self.root)
        entry_y_seq.grid(row=15, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Z:").grid(row=16, column=0, padx=5, pady=5, sticky='e')
        entry_z_seq = tk.Entry(self.root)
        entry_z_seq.grid(row=16, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Duration:").grid(row=17, column=0, padx=5, pady=5, sticky='e')
        entry_duration = tk.Entry(self.root)
        entry_duration.insert(0, "2")  # Default 

        entry_duration.grid(row=17, column=1, padx=5, pady=5)

        tk.Button(self.root, text="Add to Sequence", command=add_position_to_sequence).grid(row=18, column=0, columnspan=2, padx=5, pady=5)
        tk.Button(self.root, text="Add Current Position", command=add_current_position_to_sequence).grid(row=18, column=2, padx=5, pady=5)
        tk.Button(self.root, text="Clear Sequence", command=clear_sequence).grid(row=19, column=2, padx=5, pady=5)

        sequence_display = tk.Listbox(self.root, height=5)
        sequence_display.grid(row=20, column=0, columnspan=3, padx=5, pady=5)

        tk.Button(self.root, text="Save Sequence", command=save_sequence).grid(row=21, column=0, padx=5, pady=5)
        tk.Button(self.root, text="Load Sequence", command=load_sequence).grid(row=21, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Run Sequence", command=run_sequence).grid(row=21, column=2, padx=5, pady=5)

# Implement the add_current_position_to_sequence function

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = StepperControlApp(root)
    root.mainloop()
