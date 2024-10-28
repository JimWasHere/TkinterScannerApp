import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
import cv2
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import threading

DATA_FILE = 'inventory_data.json'

# second functional version

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management App")
        self.locations = self.load_data()
        self.cap = None  # Camera capture object
        self.barcode_processing = False  # Flag for barcode processing state

        self.create_main_screen()

    def load_data(self):
        """Load inventory data from JSON file."""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self):
        """Save inventory data to JSON file."""
        with open(DATA_FILE, 'w') as f:
            json.dump(self.locations, f, indent=4)

    def create_main_screen(self):
        """Create the main screen layout with navigation buttons."""
        for widget in self.root.winfo_children():
            widget.destroy()

        title = tk.Label(self.root, text="Inventory Management System", font=("Arial", 24))
        title.pack(pady=20)

        location_button = tk.Button(self.root, text="Manage Locations", font=("Arial", 18),
                                    command=self.go_to_location_management)
        location_button.pack(pady=10)

        scan_button = tk.Button(self.root, text="Scan Barcodes", font=("Arial", 18), command=self.go_to_scan_screen)
        scan_button.pack(pady=10)

    def go_to_scan_screen(self):
        """Navigate to the barcode scanning screen."""
        for widget in self.root.winfo_children():
            widget.destroy()

        title = tk.Label(self.root, text="Barcode Scanning", font=("Arial", 24))
        title.pack(pady=20)

        camera_button = tk.Button(self.root, text="Scan Using Camera", font=("Arial", 18),
                                  command=self.scan_barcode_with_camera)
        camera_button.pack(pady=10)

        manual_entry_button = tk.Button(self.root, text="Enter Barcode Manually", font=("Arial", 18),
                                        command=self.manual_barcode_entry)
        manual_entry_button.pack(pady=10)

        back_button = tk.Button(self.root, text="Back to Main", font=("Arial", 18), command=self.create_main_screen)
        back_button.pack(pady=10)

    def scan_barcode_with_camera(self):
        """Use the camera to scan barcodes with an embedded Close button."""
        if self.cap is not None:
            self.cap.release()  # Release previous capture if exists

        # Open a new Tkinter window for the camera feed
        self.camera_window = tk.Toplevel(self.root)
        self.camera_window.title("Barcode Scanner")

        # Create a Label to display the video feed
        self.video_label = tk.Label(self.camera_window)
        self.video_label.pack()

        # Create a Close button in the same window
        close_button = tk.Button(self.camera_window, text="Close Camera", command=self.close_camera_feed)
        close_button.pack(pady=10)

        self.cap = cv2.VideoCapture(0)  # Open the webcam
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera.")
            self.camera_window.destroy()
            return

        self.update_camera_feed()

    def update_camera_feed(self):
        """Update the camera feed within the Tkinter window."""
        ret, frame = self.cap.read()
        if ret:
            # Resize the frame to make it smaller, so it doesn't take the entire screen
            frame = cv2.resize(frame, (320, 240))  # Set desired width and height here
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            if not self.barcode_processing:
                barcodes = decode(frame)
                if barcodes:
                    barcode_data = barcodes[0].data.decode('utf-8')
                    self.barcode_processing = True
                    threading.Thread(target=self.process_scanned_barcode, args=(barcode_data,), daemon=True).start()

        if self.cap.isOpened():
            self.camera_window.after(10, self.update_camera_feed)

    def close_camera_feed(self):
        """Close the camera feed and the Tkinter camera window."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None  # Make sure cap is properly released
        self.camera_window.destroy()
        cv2.destroyAllWindows()  # Properly close any OpenCV windows
        self.barcode_processing = False  # Reset the barcode processing flag

    def manual_barcode_entry(self):
        """Allow the user to manually enter a barcode."""
        barcode = simpledialog.askstring("Enter Barcode", "Enter the barcode manually:")
        if barcode:
            self.process_scanned_barcode(barcode)

    def process_scanned_barcode(self, barcode):
        """Process the scanned or manually entered barcode."""
        found = False
        for location in self.locations:
            for shelf in self.locations[location]:
                if barcode in self.locations[location][shelf]:
                    messagebox.showinfo("Barcode Found", f"Barcode exists in {location} > {shelf}")
                    found = True
                    break

        if not found:
            messagebox.showinfo("Barcode Not Found", "The scanned barcode was not found in the system.")

        self.barcode_processing = False  # Reset the processing flag after scanning

    def go_to_location_management(self):
        """Navigate to location management screen."""
        for widget in self.root.winfo_children():
            widget.destroy()

        title = tk.Label(self.root, text="Location Management", font=("Arial", 24))
        title.pack(pady=20)

        for location in self.locations:
            location_button = tk.Button(self.root, text=f"Location: {location}", font=("Arial", 18),
                                        command=lambda loc=location: self.show_shelves(loc))
            location_button.pack(pady=5)

            delete_location_button = tk.Button(self.root, text=f"Delete {location}", font=("Arial", 14), fg="red",
                                               command=lambda loc=location: self.delete_location(loc))
            delete_location_button.pack(pady=2)

        add_location_button = tk.Button(self.root, text="Add New Location", font=("Arial", 16),
                                        command=self.add_location)
        add_location_button.pack(pady=10)

        back_button = tk.Button(self.root, text="Back to Main", font=("Arial", 16), command=self.create_main_screen)
        back_button.pack(pady=10)

    def show_shelves(self, location):
        """Show shelves for the selected location."""
        self.current_location = location
        for widget in self.root.winfo_children():
            widget.destroy()

        title = tk.Label(self.root, text=f"Shelves in {location}", font=("Arial", 24))
        title.pack(pady=20)

        for shelf in self.locations[location]:
            shelf_button = tk.Button(self.root, text=f"Shelf: {shelf}", font=("Arial", 18),
                                     command=lambda sh=shelf: self.show_nested_shelves(location, sh))
            shelf_button.pack(pady=5)

            delete_shelf_button = tk.Button(self.root, text=f"Delete {shelf}", font=("Arial", 14), fg="red",
                                            command=lambda sh=shelf: self.delete_shelf(location, sh))
            delete_shelf_button.pack(pady=2)

        add_shelf_button = tk.Button(self.root, text="Add New Shelf", font=("Arial", 16), command=self.add_shelf)
        add_shelf_button.pack(pady=10)

        back_button = tk.Button(self.root, text="Back to Locations", font=("Arial", 16),
                                command=self.go_to_location_management)
        back_button.pack(pady=10)

    def show_nested_shelves(self, location, shelf):
        """Show nested shelves for the selected shelf."""
        self.current_shelf = shelf
        for widget in self.root.winfo_children():
            widget.destroy()

        title = tk.Label(self.root, text=f"Nested Shelves in {shelf}", font=("Arial", 24))
        title.pack(pady=20)

        for nested_shelf in self.locations[location][shelf]:
            nested_shelf_button = tk.Button(self.root, text=f"Nested Shelf: {nested_shelf}", font=("Arial", 18),
                                            command=lambda ns=nested_shelf: self.show_items(location, shelf, ns))
            nested_shelf_button.pack(pady=5)

            delete_nested_shelf_button = tk.Button(self.root, text=f"Delete {nested_shelf}", font=("Arial", 14),
                                                   fg="red",
                                                   command=lambda ns=nested_shelf: self.delete_nested_shelf(location,
                                                                                                            shelf, ns))
            delete_nested_shelf_button.pack(pady=2)

        add_nested_shelf_button = tk.Button(self.root, text="Add New Nested Shelf", font=("Arial", 16),
                                            command=self.add_nested_shelf)
        add_nested_shelf_button.pack(pady=10)

        back_button = tk.Button(self.root, text="Back to Shelves", font=("Arial", 16),
                                command=lambda: self.show_shelves(location))
        back_button.pack(pady=10)

    def add_location(self):
        """Prompt user for a new location and add it."""
        new_location = simpledialog.askstring("Add Location", "Enter location name:")
        if new_location:
            self.locations[new_location] = {}
            self.save_data()
            self.go_to_location_management()

    def delete_location(self, location):
        """Delete a location and all its contents."""
        if messagebox.askyesno("Delete Location", f"Are you sure you want to delete {location} and all its contents?"):
            del self.locations[location]
            self.save_data()
            self.go_to_location_management()

    def add_shelf(self):
        """Prompt user for a new shelf and add it."""
        new_shelf = simpledialog.askstring("Add Shelf", "Enter shelf name:")
        if new_shelf and self.current_location:
            self.locations[self.current_location][new_shelf] = []
            self.save_data()
            self.show_shelves(self.current_location)

    def delete_shelf(self, location, shelf):
        """Delete a shelf and all its contents."""
        if messagebox.askyesno("Delete Shelf", f"Are you sure you want to delete {shelf} and all its contents?"):
            del self.locations[location][shelf]
            self.save_data()
            self.show_shelves(location)

    def add_nested_shelf(self):
        """Prompt user for a new nested shelf and add it."""
        new_nested_shelf = simpledialog.askstring("Add Nested Shelf", "Enter nested shelf name:")
        if new_nested_shelf and self.current_shelf and self.current_location:
            self.locations[self.current_location][self.current_shelf].append(new_nested_shelf)
            self.save_data()
            self.show_nested_shelves(self.current_location, self.current_shelf)

    def delete_nested_shelf(self, location, shelf, nested_shelf):
        """Delete a nested shelf."""
        if messagebox.askyesno("Delete Nested Shelf", f"Are you sure you want to delete {nested_shelf}?"):
            self.locations[location][shelf].remove(nested_shelf)
            self.save_data()
            self.show_nested_shelves(location, shelf)

    def show_items(self, location, shelf, nested_shelf):
        """Show the items in a nested shelf."""
        messagebox.showinfo("Items", f"Showing items in {location} > {shelf} > {nested_shelf}")


if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.geometry("600x500")
    root.mainloop()
