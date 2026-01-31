from pack2.Compare2 import Compare2
import tkinter as tk

def exit_fullscreen(event):
    root.attributes("-fullscreen", False)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)   # 开启全屏
    root.bind("<Escape>", exit_fullscreen)
    app = Compare2(root)
    root.mainloop()
    