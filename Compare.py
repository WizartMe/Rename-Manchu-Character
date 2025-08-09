import os
import tkinter as tk
from io import BytesIO
from tkinter import ttk, messagebox
import requests
from PIL import ImageTk, Image
import time

from GlobalFunc import center_window, sort_file

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

class Compare:
    def __init__(self, master, folder_path, page_name):
        self.root = master
        self.folder_path = folder_path
        self.page_name = page_name
        self.rename_lst = []
        self.imgs = []
        self.index = 0
        self.old_path = ''

        self.top_label_var = tk.StringVar()

        # 防止图片被垃圾回收
        self.left_photo_image = None
        self.right_photo_image = None

        self.root.title(f"比较页面 - {self.page_name}")
        self.root.geometry("1200x800")

        center_window(self.root)
        self._create_widgets()
        self.init_img()

    def _create_widgets(self):
        """创建界面中的所有框架和组件"""
        # 为窗口配置网格权重
        self.root.rowconfigure(0, weight=0)  # 顶部行不垂直拉伸
        self.root.rowconfigure(1, weight=1)  # 中部行(图片区域)将填充所有可用垂直空间
        self.root.rowconfigure(2, weight=0)  # 底部行不垂直拉伸
        self.root.columnconfigure(0, weight=1)  # 列的配置保持不变，允许水平拉伸

        # --- 顶部框架 ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky='ew')

        # 使用一个子框架来帮助居中
        top_center_frame = ttk.Frame(top_frame)
        top_center_frame.pack()

        top_label = ttk.Label(top_center_frame, textvariable=self.top_label_var)
        top_label.pack()

        # --- 中部框架 (包含左右两个子框架) ---
        middle_container = ttk.Frame(self.root, padding="10")
        middle_container.grid(row=1, column=0, sticky='nsew')

        # 配置中部容器的网格，使其内部两列平分宽度
        middle_container.columnconfigure(0, weight=1)
        middle_container.columnconfigure(1, weight=1)
        # 配置中部容器的行，使其能垂直拉伸
        middle_container.rowconfigure(0, weight=1)

        # 左侧框架
        left_frame = ttk.LabelFrame(middle_container, text="待检查图片", padding="10")
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        # 示例内容
        self.left_canvas = tk.Canvas(left_frame, bg="#E0E0E0", highlightthickness=0)
        self.left_canvas.grid(row=0, column=0, sticky='nsew')

        # 右侧框架
        right_frame = ttk.LabelFrame(middle_container, text="正确图片", padding="10")
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        # 示例内容
        self.right_canvas = tk.Canvas(right_frame, bg="#E0E0E0", highlightthickness=0)
        self.right_canvas.grid(row=0, column=0, sticky='nsew')

        # --- 底部框架 ---
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.grid(row=2, column=0, sticky='ew')

        # 为了让内部组件居中，我们将底部框架的列配置为三部分：空白、内容、空白
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=0)  # 内容区不拉伸
        bottom_frame.columnconfigure(2, weight=1)

        # 创建一个容器来放置所有输入和按钮，并将其放入中间的网格列
        control_container = ttk.Frame(bottom_frame)
        control_container.grid(row=0, column=1)

        # 按钮区域
        button_frame = ttk.Frame(control_container)
        button_frame.pack()

        confirm_btn = ttk.Button(button_frame, text="正确", command=self.on_confirm)
        confirm_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = ttk.Button(button_frame, text="错误", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=10)

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

    def init_img(self):
        dir_path = os.path.join(self.folder_path, self.page_name)
        if not os.path.isdir(dir_path):
            messagebox.showerror("路径错误", f"找不到页面文件夹：\n{dir_path}")
            self.root.destroy()
            return

        self.imgs = sorted(os.listdir(dir_path), key=sort_file)

        while self.index < len(self.imgs) and (
                self.imgs[self.index].startswith("0") or self.imgs[self.index].startswith("1")):
            self.index += 1

        if self.index >= len(self.imgs):
            messagebox.showinfo("任务完成", "此页面的所有图片均已检查完毕！")
            self.root.destroy()
            return

        self.old_path = os.path.join(dir_path, self.imgs[self.index])
        try:
            file_name, _ = os.path.splitext(self.old_path)
            word_str = file_name.split("_")[-1].replace('ū', 'v').replace('š', 'x').replace('ž', 'z')
        except Exception as e:
            messagebox.showerror("文件读取错误", f"读取list.txt时发生错误: {e}")
            self.root.destroy()
            return

        self.top_label_var.set(f"当前页面：{self.page_name}\t当前文字：{file_name}")
        self.load_local_image(self.old_path)
        self.load_remote_image(word_str)

    def _go_to_next_image(self):
        """处理进入下一张图片的逻辑"""
        if self.index >= len(self.imgs) - 1:
            messagebox.showinfo("任务完成", "此页面的所有图片均已检查完毕！")
            self.root.destroy()
            return

        self.index += 1
        self.init_img()

    def on_confirm(self):
        """标记为'正确'并处理文件"""
        try:
            dir_path, filename = os.path.split(self.old_path)
            new_filename = '0' + filename
            new_path = os.path.join(dir_path, new_filename)
            os.rename(self.old_path, new_path)
            print(f"文件重命名: {filename} -> {new_filename}")
        except Exception as e:
            messagebox.showerror("文件错误", f"重命名文件时出错: {e}")
            self.root.destroy()
            return

        self._go_to_next_image()

    def on_cancel(self):
        """标记为'错误'并处理文件"""
        try:
            dir_path, filename = os.path.split(self.old_path)
            new_filename = '1' + filename
            new_path = os.path.join(dir_path, new_filename)
            os.rename(self.old_path, new_path)
            print(f"文件重命名: {filename} -> {new_filename}")
        except Exception as e:
            messagebox.showerror("文件错误", f"重命名文件时出错: {e}")
            self.root.destroy()
            return

        self._go_to_next_image()