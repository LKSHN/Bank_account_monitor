'''
 # @ Author: Eshino
 # @ Create Time: 2025-05-08 21:21:58
 # @ Modified by: Eshino
 # @ Modified time: 2025-05-08 23:45:52
 # @ Description: Main frame holding the program
 '''

import tkinter as tk

def create_main_window():
    #Create window
    root = tk.Tk()
    root.title("Openfront.io Dashboard")
    root.geometry("820x600")
    root.protocol("WM_DELETE_WINDOW", root.quit)
    return (root)

def main():
    # Create main window
    root = create_main_window()
    
    #Run tkinter loop
    root.mainloop()

    return 0

if __name__ == "__main__":
    main()