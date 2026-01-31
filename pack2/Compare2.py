import os
import tkinter as tk
from io import BytesIO
from tkinter import ttk, messagebox
from tkinter import filedialog
import requests
from PIL import ImageTk, Image
import time

from pack2.GlobalFunc import center_window, file_sort_key

max_retries = 3
retry_delay = 2

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Host': 'anakv.anakv.com',
    'Origin': 'http://anakv.anakv.com',
    'Referer': 'http://anakv.anakv.com/msc.html',
}
params = {
    "input": '',
    "font": "1",
    "wpc": "5",
    "fontsize": "25",
    "cspace": "10",
    "fcolor": "Black",
    "bcolor": "White"
}

session = requests.Session()  # 创建会话对象
session.headers.update(headers)  # 会话设置统一 headers
session.get("http://anakv.anakv.com/")
time.sleep(1)

class Compare2:
    def __init__(self, master):
        self.root = master
        self.folder_path = ''
        self.page_names = []
        self.page_name = ''
        self.rename_lst = []
        self.imgs = []
        self.index = 0
        self.old_path = ''

        self.col = tk.StringVar(value=1)
        self.row = tk.StringVar(value=1)

        # 防止图片被垃圾回收
        self.left_photo_image = None
        self.right_photo_image = None

        self.root.title(f"比较工具")
        self.root.geometry("1200x800")

        center_window(self.root)
        self._create_widgets()

    def _create_widgets(self):
        """创建界面中的所有框架和组件"""
        # 为窗口配置网格权重
        self.root.rowconfigure(0, weight=0)  # 顶部行不垂直拉伸
        self.root.rowconfigure(1, weight=1)  # 中部行(图片区域)填充可用空间
        self.root.rowconfigure(2, weight=0)  # 底部行不垂直拉伸
        self.root.columnconfigure(0, weight=1)  # 整体横向拉伸

        # --- 顶部框架 ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky='ew')

        top_center_frame = ttk.Frame(top_frame)
        top_center_frame.pack()
        ttk.Label(top_center_frame, text="导入文件夹:").grid(row=0, column=0, sticky=tk.E)
        self.entry_dir = ttk.Entry(top_center_frame, width=30)
        self.entry_dir.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.button_browse = ttk.Button(top_center_frame, text="浏览", command=self.browse_directory)
        self.button_browse.grid(row=0, column=2, sticky=tk.W)
        ttk.Label(top_center_frame, text="Page文件夹:").grid(row=0, column=3, sticky=tk.E, padx=5)
        self.combobox = ttk.Combobox(top_center_frame, state="readonly", width=20)
        self.combobox.grid(row=0, column=4, padx=5)
        self.combobox.bind("<<ComboboxSelected>>", self._sel_page)

        # --- 中部框架 ---
        middle_container = ttk.Frame(self.root, padding="10")
        middle_container.grid(row=1, column=0, sticky='nsew')

        # 比例改为 12:5:3 (大约 60%:25%:15%)
        middle_container.columnconfigure(0, weight=6, uniform='col')
        middle_container.columnconfigure(1, weight=2, uniform='col')
        middle_container.columnconfigure(2, weight=2, uniform='col')
        middle_container.rowconfigure(0, weight=1)

        # 左侧框架
        left_frame = ttk.LabelFrame(middle_container, text="原始图片", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        self.ori_canvas = tk.Canvas(left_frame, bg="#E0E0E0", highlightthickness=0)
        self.ori_canvas.grid(row=0, column=0, sticky="nsew")
        self.left_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.ori_canvas.yview)
        self.ori_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        self.left_scrollbar.grid(row=0, column=1, sticky="ns")
        # 绑定鼠标滚轮事件到 Canvas
        def _on_mouse_wheel(event):
            self.ori_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.ori_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)   # Windows
        self.ori_canvas.bind_all("<Button-4>", lambda e: self.ori_canvas.yview_scroll(-1, "units"))  # Linux 上滚
        self.ori_canvas.bind_all("<Button-5>", lambda e: self.ori_canvas.yview_scroll(1, "units"))   # Linux 下滚


        # 中部框架
        mid_frame = ttk.LabelFrame(middle_container, text="待检查图片", padding="5")
        mid_frame.grid(row=0, column=1, sticky="nsew")
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.rowconfigure(0, weight=1)
        self.left_canvas = tk.Canvas(mid_frame, bg="#E0E0E0", highlightthickness=0)
        self.left_canvas.grid(row=0, column=0, sticky="nsew")

        # 右侧框架
        right_frame = ttk.LabelFrame(middle_container, text="正确图片", padding="5")
        right_frame.grid(row=0, column=2, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        self.right_canvas = tk.Canvas(right_frame, bg="#E0E0E0", highlightthickness=0)
        self.right_canvas.grid(row=0, column=0, sticky="nsew")

        # --- 底部框架 ---
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.grid(row=2, column=0, sticky='ew')

        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=0)
        bottom_frame.columnconfigure(2, weight=1)

        ipt_container = ttk.Frame(bottom_frame)
        ipt_container.grid(row=0, column=1, pady=10)

        self.lbl_col = ttk.Label(ipt_container, text="列：")
        self.ipt_col = ttk.Entry(ipt_container, textvariable=self.col, width=10)
        self.lbl_col.grid(row=0, column=1)
        self.ipt_col.grid(row=0, column=2, padx=8)
        self.lbl_row = ttk.Label(ipt_container, text="行：")
        self.ipt_row = ttk.Entry(ipt_container, textvariable=self.row, width=10)
        self.lbl_row.grid(row=0, column=3)
        self.ipt_row.grid(row=0, column=4, padx=8)
        self.col_btn = ttk.Button(ipt_container, text="增加列", command=self._add_col)
        self.row_btn = ttk.Button(ipt_container, text="增加行", command=self._add_row)
        self.col_btn.grid(row=0, column=5, padx=8)
        self.row_btn.grid(row=0, column=6, padx=8)

        control_container = ttk.Frame(bottom_frame)
        control_container.grid(row=1, column=1, pady=10)

        button_frame = ttk.Frame(control_container)
        button_frame.pack()

        confirm_btn = ttk.Button(button_frame, text="正确", command=self.on_confirm)
        confirm_btn.pack(side=tk.LEFT, padx=10)
        cancel_btn = ttk.Button(button_frame, text="错误", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        del_btn = ttk.Button(button_frame, text="删除", command=self.del_file)
        del_btn.pack(side=tk.LEFT, padx=10)

    def init_page_img(self):
        path = os.path.join(self.folder_path, f"{self.page_name}.png")
        img_pil = Image.open(path)
        canvas_width = self.ori_canvas.winfo_width()

        if canvas_width <= 1:
            self.ori_canvas.after(100, self.init_page_img)
            return

        # 按宽度缩放
        img_width, img_height = img_pil.size
        img_ratio = img_width / img_height

        new_width = canvas_width
        new_height = int(canvas_width / img_ratio)

        resized_img = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized_img)  # 🔹 保存引用

        self.ori_canvas.delete("all")
        # 顶部居中显示（x 居中，y 从 0 开始）
        self.ori_canvas.create_image(canvas_width / 2, 0, anchor=tk.N, image=self.photo_image)

        # 设置滚动区域
        self.ori_canvas.config(scrollregion=(0, 0, new_width, new_height))

    def browse_directory(self):
        dir_path = filedialog.askdirectory(title="选择文件夹（如：E:/ID-Name）")
        self.folder_path = dir_path
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
                self._sel_page()
        else:
            messagebox.showerror("错误", "选择的路径不是一个有效的文件夹")

    def _sel_page(self, event=None):
        self.page_name = self.combobox.get()
        self.index = 0
        path = os.path.join(self.folder_path, f"{self.page_name}.txt").replace('\\','/')
        self.rename_lst = self.read_rename_txt(path)
        self.init_page_img()
        dir_paths = os.path.join(self.folder_path, self.page_name)
        self.imgs = sorted(os.listdir(dir_paths), key=file_sort_key)
        self.init_img()
        self.col.set(1)
        self.row.set(1)

    def _display_image_on_canvas(self, canvas, img_pil):
        """在Canvas上显示图片，自动缩放并居中，支持放大"""
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas.after(100, lambda: self._display_image_on_canvas(canvas, img_pil))
            return

        # 计算缩放比例
        img_width, img_height = img_pil.size
        canvas_ratio = canvas_width / canvas_height
        img_ratio = img_width / img_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)

        resized_img = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo_image = ImageTk.PhotoImage(resized_img)

        canvas.delete("all")
        canvas.create_image(canvas_width / 2, canvas_height / 2, anchor=tk.CENTER, image=photo_image)

        if canvas == self.left_canvas:
            self.left_photo_image = photo_image
        else:
            self.right_photo_image = photo_image

    def load_local_image(self, image_path):
        """从本地路径加载图片并显示在左侧Canvas"""
        try:
            img_pil = Image.open(image_path)
            self._display_image_on_canvas(self.left_canvas, img_pil)
        except FileNotFoundError:
            print(f"错误：本地图片未找到于 {image_path}")
        except Exception as e:
            print(f"加载本地图片时出错: {e}")

    def load_remote_image(self, word_str):
        params['input'] = word_str
        for attempt in range(max_retries):
            try:
                # 发送GET请求，并设置一个合理的超时时间（例如10秒）
                response = session.get('http://anakv.anakv.com/msc.php', params=params, stream=True, timeout=10, verify=False)
                response.raise_for_status()  # 如果状态码不是2xx，则引发HTTPError
                 # 先检查响应内容类型，确保是图片
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image'):
                    print(f"返回内容不是图片，Content-Type: {content_type}")
                    raise ValueError("返回内容不是图片")
                
                # 请求成功，处理图片并跳出循环
                image_data = BytesIO(response.content)
                img_pil = Image.open(image_data)
                self._display_image_on_canvas(self.right_canvas, img_pil)
                return  # 成功加载后直接返回

            except requests.exceptions.RequestException as e:
                print(f"网络请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    # 这是最后一次尝试，跳出循环后将执行失败逻辑
                    continue

        # 如果循环正常结束（即所有重试都失败了），则执行以下代码
        messagebox.showerror(
            "严重网络错误",
            f"无法从服务器获取图片 '{word_str}'。\n\n"
            "请检查您的网络连接或确认服务器状态，然后重启程序。"
        )
        self.root.destroy()  # 安全地关闭窗口并退出程序

    def read_rename_txt(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        res = [line.strip().split("：")[-1] for line in lines]
        return sorted(res,key=file_sort_key)

    def init_img(self):
        dir_path = os.path.join(self.folder_path, self.page_name)
        if not os.path.isdir(dir_path):
            messagebox.showerror("路径错误", f"找不到页面文件夹：\n{dir_path}")
            self.root.destroy()
            return
        while self.index < len(self.imgs) and ('_' in self.imgs[self.index]):
            self.index += 1

        if self.index >= len(self.imgs):
            messagebox.showinfo("任务完成", "此页面的所有图片均已检查完毕！")
            return

        self.old_path = os.path.join(dir_path, self.imgs[self.index])
        try:
            _, filename = os.path.split(self.old_path)
            index = int(filename.split('.')[0])-1
            word_str = self.rename_lst[index].replace('ū', 'v').replace('š', 'x').replace('ž', 'z')
        except Exception as e:
            messagebox.showerror("文件读取错误", f"读取list.txt时发生错误: {e}")
            self.root.destroy()
            return

        self.load_local_image(self.old_path)
        self.load_remote_image(word_str)

    def _go_to_next_image(self):
        """处理进入下一张图片的逻辑"""
        if self.index >= len(self.imgs) - 1:
            messagebox.showinfo("任务完成", "此页面的所有图片均已检查完毕！")
            return
        self.index += 1
        self.init_img()

    def on_confirm(self):
        """标记为'正确'并处理文件"""
        try:
            dir_path, filename = os.path.split(self.old_path)
            page = self.page_name.split('_')[-1]
            col = int(self.col.get())
            row = int(self.row.get())
            new_filename = f"0_{page}_{col}_{row}_{self.rename_lst[self.index]}.png"
            new_path = os.path.join(dir_path, new_filename)
            os.rename(self.old_path, new_path)
            print(f"文件重命名: {filename} -> {new_filename}")
        except Exception as e:
            messagebox.showerror("文件错误", f"重命名文件时出错: {e}")
            self.root.destroy()
            return
        
        self._add_row()
        self._go_to_next_image()

    def on_cancel(self):
        """标记为'错误'并处理文件"""
        try:
            dir_path, filename = os.path.split(self.old_path)
            page = self.page_name.split('_')[-1]
            col = int(self.col.get())
            row = int(self.row.get())
            new_filename = f"1_{page}_{col}_{row}_{self.rename_lst[self.index]}.png"
            new_path = os.path.join(dir_path, new_filename)
            os.rename(self.old_path, new_path)
            print(f"文件重命名: {filename} -> {new_filename}")
        except Exception as e:
            messagebox.showerror("文件错误", f"重命名文件时出错: {e}")
            self.root.destroy()
            return

        self._add_row()
        self._go_to_next_image()

    def del_file(self):
        os.remove(self.old_path)
        self._go_to_next_image()
    
    def _add_col(self):
        value = int(self.col.get() or 0)  # 从 StringVar 取值
        self.col.set(value + 1)           # 设置回去
        self.row.set(1)

    def _add_row(self):
        value = int(self.row.get() or 0)
        self.row.set(value + 1)
