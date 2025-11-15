import tkinter as tk
from tkinter import messagebox, Menu, Listbox

def on_categorize():
    selection = listbox.curselection()
    if selection:
        email = listbox.get(selection[0])
        messagebox.showinfo("Categorized", f"Email '{email}' categorized!")

root = tk.Tk()
root.title("Email Categorizer")

# Menu
menu = Menu(root)
file_menu = Menu(menu, tearoff=0)
file_menu.add_command(label="Exit", command=root.quit)
menu.add_cascade(label="File", menu=file_menu)
root.config(menu=menu)

# Listbox with emails
listbox = Listbox(root, width=40)
emails = ["Email 1: Subject A", "Email 2: Subject B", "Email 3: Subject C"]
for email in emails:
    listbox.insert(tk.END, email)
listbox.pack(pady=10)

# Button
btn = tk.Button(root, text="Categorize", command=on_categorize)
btn.pack(pady=5)

root.mainloop()
