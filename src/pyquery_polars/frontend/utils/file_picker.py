import tkinter as tk
from tkinter import filedialog
import os

def pick_file(title="Select File", file_types=None):
    """
    Opens a native file selection dialog.
    
    Args:
        title: Dialog title
        file_types: List of tuples e.g. [("CSV Files", "*.csv"), ("All Files", "*.*")]
        
    Returns:
        Selected file path string or None if cancelled
    """
    if file_types is None:
        file_types = [("All Files", "*.*")]
        
    root = tk.Tk()
    root.withdraw() # Hide the main window
    root.wm_attributes('-topmost', 1) # Ensure dialog is on top
    
    try:
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=file_types
        )
        return file_path if file_path else None
    except Exception as e:
        print(f"File picker error: {e}")
        return None
    finally:
        root.destroy()

def pick_folder(title="Select Folder"):
    """
    Opens a native folder selection dialog.
    
    Args:
        title: Dialog title
        
    Returns:
        Selected folder path string or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    
    try:
        folder_path = filedialog.askdirectory(title=title)
        return folder_path if folder_path else None
    except Exception as e:
        print(f"Folder picker error: {e}")
        return None
    finally:
        root.destroy()
