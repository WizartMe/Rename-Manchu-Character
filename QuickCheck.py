import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from GlobalFunc import file_sort_key, center_window, write_txt, read_txt
from FileSort import FileSorterApp

class QuickCheckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quick Check")
        self.root_dir = ""
        self.page_names = []
        self.en_col_var = tk.StringVar(value='8')
        self.entry_label_var = tk.StringVar(value="输入第1列文字个数: ")
        self.rows_lst = []

        center_window(self.root, width_ratio=0.6, height_ratio=0.8)
        self.create_widgets()

    def create_widgets(self):
        print("正在初始化 QuickCheck 应用...")
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=4)
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.rowconfigure(3, weight=1)

        # 导入文件夹(E:/ID-Name)
        dir_frame = ttk.Frame(self.main_frame)
        dir_frame.pack()
        ttk.Label(dir_frame, text="导入文件夹:").grid(row=0, column=0, sticky=tk.E)
        self.entry_dir = ttk.Entry(dir_frame, width=30)
        self.entry_dir.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.button_browse = ttk.Button(dir_frame, text="浏览", command=self.browse_directory)
        self.button_browse.grid(row=0, column=2, sticky=tk.W)
        ttk.Label(dir_frame, text="Page文件夹:").grid(row=0, column=3, sticky=tk.E, padx=5)
        self.combobox = ttk.Combobox(dir_frame, state="readonly", width=20)
        self.combobox.grid(row=0, column=4, padx=5)
        self.combobox.bind("<<ComboboxSelected>>", self.update_image)

        # 显示书籍页面图片
        image_frame = ttk.Frame(self.main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.canvas = tk.Canvas(image_frame, bg="systemWindow", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self.resize_image)
        
        # 输入行列
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        ttk.Label(input_frame, text="输入列数:").grid(row=0, column=0, sticky=tk.W)
        self.entry_columns = ttk.Entry(input_frame, width=10, textvariable=self.en_col_var)
        self.entry_columns.grid(row=0, column=1, sticky=tk.W)
        self.entry_col_button = ttk.Button(input_frame, text="确认", command=self.set_columns)
        self.entry_columns.bind("<Return>", lambda event: self.set_columns())
        self.entry_col_button.grid(row=0, column=2, sticky=tk.W)
        ttk.Label(input_frame, textvariable=self.entry_label_var).grid(row=1, column=0, sticky=tk.W)
        self.entry_rows = ttk.Entry(input_frame, width=10)
        self.entry_rows.grid(row=1, column=1, sticky=tk.W)
        self.entry_row_button = ttk.Button(input_frame, text="确认", command=self.set_rows)
        self.entry_rows.bind("<Return>", lambda event: self.set_rows())
        self.entry_row_button.grid(row=1, column=2, sticky=tk.W)
        self.last_col_button = ttk.Button(input_frame, text="上一步", command=self.previous_page)
        self.last_col_button.grid(row=1, column=3, sticky=tk.W)
        self.entry_rows.config(state='disabled')
        self.entry_row_button.config(state='disabled')
        self.last_col_button.config(state='disabled')

        # 绑定窗口关闭事件，检查按钮
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.pack()
        self.check_button = ttk.Button(bottom_frame, text="记录行列", command=self.check_button).grid(row=0, column=0, sticky=tk.E)
        self.change_widget_button = ttk.Button(bottom_frame, text="切换到文件排序", command=self.change_widget).grid(row=0, column=1, sticky=tk.E, padx=10)

    def browse_directory(self):
        dir_path = tk.filedialog.askdirectory(title="选择文件夹（如：E:/ID-Name）")
        self.root_dir = dir_path
        if os.path.isdir(dir_path):
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, dir_path)
            self.page_names = []  # 清空之前的页面名称列表

            for f in os.listdir(dir_path):
                if f.startswith('page_') and '.' not in f:
                    self.page_names.append(f)
            
            if not self.page_names:
                messagebox.showwarning("警告", "没有找到以 'page_' 开头的文件夹")
                return 
            else:
                self.page_names.sort(key=file_sort_key)
                self.combobox['values'] = self.page_names
                self.combobox.current(0)
                self.update_image(None)
                self.first_rename()
        else:
            messagebox.showerror("错误", "选择的路径不是一个有效的文件夹")

    def resize_image(self, event=None):
        if event:
            self.update_image(event)  # 调用更新图像的逻辑

    def update_image(self, event):
        if not self.page_names:
            return
        
        page_name = self.combobox.get()
        dir_path = self.root_dir
        image_path = os.path.join(dir_path, f"{page_name}.png")
        self.canvas.delete("all")  # 清除画布上的所有元素
        if os.path.exists(image_path):
            img = Image.open(image_path)  # 使用Pillow加载图片
            original_width, original_height = img.size  # 获取原始图像的尺寸
            aspect_ratio = original_width / original_height  # 原始图像的纵横比
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width / height > aspect_ratio:  # 根据高度调整宽度
                new_height = height
                new_width = int(new_height * aspect_ratio)
            else:  # 根据宽度调整高度
                new_width = width
                new_height = int(new_width / aspect_ratio)
            resized_img = img.resize((new_width, new_height))  # 根据事件大小调整图像
            photo_img = ImageTk.PhotoImage(resized_img)  # 将Pillow图像转换为Tkinter兼容的格式
            self.canvas.create_image(width / 2, height / 2, image=photo_img, anchor=tk.CENTER)
            self.canvas.img = photo_img
        else:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            self.canvas.create_text(width / 2, height / 2, text="图片不存在", fill="red", font=("Arial", 16))
            return

    def set_columns(self):
        try:
            if not self.root_dir:
                raise ValueError("请先选择文件夹")
            self.en_col_var = int(self.entry_columns.get())
            if self.en_col_var <= 0:
                raise ValueError("列数必须大于0")
            self.entry_columns.config(state='disabled')  # 禁用输入框
            self.entry_col_button.config(state='disabled')  # 禁用按钮
            self.entry_rows.config(state='normal')
            self.entry_row_button.config(state='normal')
        except ValueError as e:
            messagebox.showerror("错误", f"无效的列数: {e}")
            self.en_col_var = tk.StringVar(value='8')  # 重置为默认值

    def set_rows(self):
        try:
            rows = int(self.entry_rows.get())
            if rows <= 0:
                raise ValueError("行数必须大于0")
            self.rows_lst.append(rows)
            index = len(self.rows_lst)
            if index >= self.en_col_var:
                self.entry_label_var.set("已输入所有列的行数")
                self.entry_rows.config(state='disabled')
                self.entry_row_button.config(state='disabled')  # 禁用按钮
                return
            self.entry_rows.delete(0, tk.END)  # 清空输入框
            self.entry_label_var.set(f"输入第{index+1}列文字个数: ")
            self.last_col_button.config(state='normal')
        except ValueError as e:
            messagebox.showerror("错误", f"无效的行数: {e}")

    def previous_page(self):
        index = len(self.rows_lst)
        if index > 0:
            index -= 1
            self.entry_label_var.set(f"输入第{index + 1}列文字个数: ")
            self.entry_rows.delete(0, tk.END)  # 清空输入框
            self.rows_lst.pop()
            if index == 0:
                self.last_col_button.config(state='disabled')
        if index < self.en_col_var:
            self.entry_rows.config(state='normal')
            self.entry_row_button.config(state='normal')

    def first_rename(self):
        page_path = os.path.join(self.root_dir, self.combobox.get())
        txt_path = os.path.join(self.root_dir, f"{self.combobox.get()}.txt")
        page_names = sorted(os.listdir(page_path), key=file_sort_key)
        if not page_names:
            messagebox.showwarning("警告", "该页面没有文件")
            return
        if '-' in page_names[0] or '_' in page_names[0]:
            return
        txt_lst = read_txt(txt_path)
        if not txt_lst:
            messagebox.showwarning("警告", "该页面没有对应的txt文件")
            return
        for old_name,text in zip(page_names, txt_lst):
            prefix = old_name.split('.')[0]
            suffix = text.split('：')[-1]
            new_name = f"{prefix}-{suffix}.png"
            os.rename(os.path.join(page_path, old_name), os.path.join(page_path, new_name))

    def check_button(self):
        if not self.root_dir:
            messagebox.showerror("错误", "请先选择文件夹")
            return
        page_name = self.combobox.get()
        if not page_name:
            messagebox.showwarning("警告", "请先选择Page文件夹")
            return
        record_fpath = os.path.join(self.root_dir, f"{page_name}-position.txt")
        if os.path.exists(record_fpath):
            if not messagebox.askyesno("提示", f"已存在 {record_fpath} 文件，是否覆盖？"):
                return
        if not self.rows_lst:
            messagebox.showwarning("警告", "请先输入行数")
            return  
        if len(self.rows_lst) != self.en_col_var:
            messagebox.showwarning("警告", f"请确保输入的行数与列数({self.en_col_var})一致")
            return
        word_num = sum(self.rows_lst)
        show_num = len(os.listdir(os.path.join(self.root_dir, page_name)))
        pos_lst = []

        for i,row in enumerate(self.rows_lst):
            for j in range(row):
                pos_lst.append(f"{i+1}_{j+1}")
        
        write_txt(record_fpath, pos_lst)
        messagebox.showinfo("提示", f"共有{word_num}个文字，共{show_num}张图片，已保存位置信息到 {page_name}-position.txt 文件中")
        
    def change_widget(self):
        self.root.destroy()  # 销毁当前窗口
        new_window = tk.Tk()
        FileSorterApp(new_window, self.root_dir, self.page_names)
        new_window.mainloop()  # 启动新的窗口的事件循环

if __name__ == "__main__":
    root = tk.Tk()
    app = QuickCheckApp(root)
    root.mainloop()