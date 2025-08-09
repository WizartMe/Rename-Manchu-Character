import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from Compare import Compare
from GlobalFunc import *

class FileSorterApp:
    def __init__(self, root, root_dir, page_names):
        self.root = root
        self.root.title("文件排序工具")

        # --- 状态变量 ---
        self.main_folder_path = root_dir
        self.page_list, self.file_list, self.moves = page_names, [], []
        self.left_img_path, self.right_img_path = None, None
        self.left_photo_image, self.right_photo_image = None, None
        self.positions = []
        self.column_count_var = tk.StringVar(value='8')
        self.single_input_var = tk.StringVar()
        self.grid_status_var = tk.StringVar()
        self.target_column_count = 0
        self.collected_row_counts = []
        self.current_column_input_index = 0

        self._create_widgets()
        center_window(self.root, width_ratio=0.6, height_ratio=0.8)
        self.page_combo['values'] = self.page_list
        self.page_combo.current(0)
        self._on_page_select(None)

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(2, weight=5)
        self.main_frame.rowconfigure(1, weight=1)

        # --- 顶部和预览区 ---
        top_frame = ttk.Frame(self.main_frame)
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        ttk.Label(top_frame, text="选择页面:").pack(side=tk.LEFT, padx=(10, 5))
        self.page_combo = ttk.Combobox(top_frame, state="readonly", width=20)
        self.page_combo.pack(side=tk.LEFT)
        self.page_combo.bind('<<ComboboxSelected>>', self._on_page_select)

        # --- 左侧文件列表 ---
        self.list_frame = ttk.LabelFrame(self.main_frame, text="页面文件列表")
        self.list_frame.grid(row=1, column=0, sticky="nswe", padx=(0, 5))
        self.list_frame.rowconfigure(0, weight=1)
        self.file_listbox = tk.Listbox(self.list_frame)
        self.file_listbox.grid(row=0, column=0, sticky="nswe")
        list_scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.file_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=list_scrollbar.set)
        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)
        self.canvas_left_frame = ttk.LabelFrame(self.main_frame, text="选中文件预览")
        self.canvas_left_frame.grid(row=1, column=1, sticky="nswe", padx=5)
        self.canvas_left = tk.Canvas(self.canvas_left_frame, bg="systemWindow", highlightthickness=0)
        self.canvas_left.pack(fill=tk.BOTH, expand=True)
        self.canvas_left_frame.bind('<Configure>', self._redraw_left_image)
        self.canvas_right_frame = ttk.LabelFrame(self.main_frame, text="Page 预览")
        self.canvas_right_frame.grid(row=1, column=2, sticky="nswe", padx=(5, 0))
        self.canvas_right = tk.Canvas(self.canvas_right_frame, bg="systemWindow", highlightthickness=0)
        self.canvas_right.pack(fill=tk.BOTH, expand=True)
        self.canvas_right_frame.bind('<Configure>', self._redraw_right_image)

        # --- 底部控制面板 ---
        control_frame = ttk.LabelFrame(self.main_frame, text="操作面板")
        control_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        main_controls_container = ttk.Frame(control_frame)
        main_controls_container.pack(fill='x', expand=True)

        # --- 阶段一：文件排序面板 ---
        self.reordering_frame = ttk.Frame(main_controls_container, padding=5)
        self.reordering_frame.pack(fill="x", pady=(0, 10))
        row1_frame = ttk.Frame(self.reordering_frame)
        row1_frame.pack(fill="x")
        delete_frame = ttk.Frame(row1_frame)
        delete_frame.pack(side=tk.LEFT, padx=(0, 20))
        self.delete_label = ttk.Label(delete_frame, text="删除文件编号:")
        self.delete_label.pack(side=tk.LEFT)
        self.delete_entry = ttk.Entry(delete_frame, width=10)
        self.delete_entry.pack(side=tk.LEFT, padx=5)
        self.delete_entry.bind('<Return>', lambda e: self._delete_file())
        self.delete_button = ttk.Button(delete_frame, text="删除", command=self._delete_file)
        self.delete_button.pack(side=tk.LEFT)
        move_frame = ttk.Frame(row1_frame)
        move_frame.pack(side=tk.LEFT)
        self.move_label1 = ttk.Label(move_frame, text="移动块 从:")
        self.move_label1.pack(side=tk.LEFT)
        self.start_entry = ttk.Entry(move_frame, width=10)
        self.start_entry.pack(side=tk.LEFT, padx=5)
        self.move_label2 = ttk.Label(move_frame, text="到:")
        self.move_label2.pack(side=tk.LEFT)
        self.end_entry = ttk.Entry(move_frame, width=10)
        self.end_entry.pack(side=tk.LEFT, padx=5)
        self.move_label3 = ttk.Label(move_frame, text="至新位置:")
        self.move_label3.pack(side=tk.LEFT)
        self.dest_entry = ttk.Entry(move_frame, width=10)
        self.dest_entry.pack(side=tk.LEFT, padx=5)
        self.add_move_button = ttk.Button(move_frame, text="添加移动指令", command=self._add_move)
        self.add_move_button.pack(side=tk.LEFT, padx=10)
        moves_list_frame = ttk.Frame(self.reordering_frame)
        moves_list_frame.pack(fill="x", expand=True, pady=5)
        self.moves_listbox = tk.Listbox(moves_list_frame, height=3)
        self.moves_listbox.pack(fill="x", expand=True)
        execute_reorder_frame = ttk.Frame(self.reordering_frame)
        execute_reorder_frame.pack(fill="x")
        self.execute_moves_button = ttk.Button(execute_reorder_frame, text="执行所有移动",command=self._execute_all_moves)
        self.execute_moves_button.pack(side=tk.LEFT)
        self.clear_moves_button = ttk.Button(execute_reorder_frame, text="清空指令", command=self._clear_moves)
        self.clear_moves_button.pack(side=tk.LEFT, padx=10)
        remove_nexist_frame = ttk.Frame(self.reordering_frame)
        remove_nexist_frame.pack(fill="x", pady=5)
        ttk.Label(remove_nexist_frame, text="移除不存在文件:").pack(side=tk.LEFT)
        ttk.Label(remove_nexist_frame, text="列：").pack(side=tk.LEFT)
        self.column_entry = ttk.Entry(remove_nexist_frame, width=10)
        self.column_entry.pack(side=tk.LEFT, padx=5)
        self.column_entry.bind('<Return>', lambda event: self._remove_nexist())
        ttk.Label(remove_nexist_frame, text="行：").pack(side=tk.LEFT)
        self.row_entry = ttk.Entry(remove_nexist_frame, width=10)
        self.row_entry.pack(side=tk.LEFT, padx=5)
        self.row_entry.bind('<Return>', lambda event: self._remove_nexist())
        self.remove_nexist_button = ttk.Button(remove_nexist_frame, text="移除", command=self._remove_nexist)
        self.remove_nexist_button.pack(side=tk.LEFT, padx=5)

        # --- 最终流程控制面板 ---
        workflow_frame = ttk.Frame(control_frame)
        workflow_frame.pack()
        self.rename_btn = ttk.Button(workflow_frame, text="自动重命名", command=self._rename_start).grid(row=0, column=0, padx=5)
        self.to_compare_button = ttk.Button(workflow_frame, text="下一步", command=self._to_compare).grid(row=0, column=1, padx=5)

    def _redraw_left_image(self, event=None):
        if self.left_img_path:
            self._display_image_on_canvas(self.canvas_left, self.left_img_path, "left")

    def _redraw_right_image(self, event=None):
        if self.right_img_path:
            self._display_image_on_canvas(self.canvas_right, self.right_img_path, "right")

    def _on_page_select(self, event=None):
        page_name = self.page_combo.get()
        if not page_name:
            return
        page_path = os.path.join(self.main_folder_path, page_name)
        self.positions = read_txt(os.path.join(self.main_folder_path, f"{page_name}-position.txt"))
        self._load_files_from_page(page_path)
        self._clear_moves()
        self.left_img_path = None
        self.canvas_left.delete("all")
        # 延迟调用，让界面先渲染
        self.root.after(50, lambda: self._display_right_page_image(page_name))

    def _load_files_from_page(self, page_path):
        self.file_listbox.delete(0, tk.END)
        self.file_list.clear()
        if not os.path.isdir(page_path):
            return
        self.file_list = sorted(os.listdir(page_path), key=sort_file)
        for file_name in self.file_list:
            self.file_listbox.insert(tk.END, file_name)

    def _display_right_page_image(self, page_name):
        img_path = os.path.join(self.main_folder_path, f"{page_name}.png")
        self._display_image_on_canvas(self.canvas_right, img_path, "right")

    def _on_file_select(self, event=None):
        page_name = self.page_combo.get()
        if not self.file_listbox.curselection():
            return
        page_path = os.path.join(self.main_folder_path, page_name)
        file_name = self.file_list[self.file_listbox.curselection()[0]]
        img_path = os.path.join(page_path, file_name)
        self._display_image_on_canvas(self.canvas_left, img_path, "left")

    def _display_image_on_canvas(self, canvas, img_path, side):
        if side == "left":
            self.left_img_path = img_path
        else:
            self.right_img_path = img_path
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return
        canvas.delete("all")
        if not os.path.exists(img_path):
            canvas.create_text(canvas_width / 2, canvas_height / 2, text="图片不存在", anchor=tk.CENTER)
            return
        try:
            img_pil = Image.open(img_path)
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
            canvas.create_image(canvas_width / 2, canvas_height / 2, anchor=tk.CENTER, image=photo_image)
            if side == "left":
                self.left_photo_image = photo_image
            else:
                self.right_photo_image = photo_image
        except (IOError, SyntaxError) as e:
            canvas.create_text(canvas_width / 2, canvas_height / 2, text=f"无法预览\n{e}", anchor=tk.CENTER)

    def _get_current_page_path(self):
        page_name = self.page_combo.get()
        if not page_name:
            messagebox.showerror("错误", "请先选择一个页面！")
            return None
        return os.path.join(self.main_folder_path, page_name)

    def _delete_file(self):
        page_path = self._get_current_page_path()
        if not page_path:
            return
        num_str = self.delete_entry.get()
        if not num_str.isdigit():
            messagebox.showwarning("警告", "请输入有效的数字编号。")
            return
        target_file = next((f for f in self.file_list if f.split('-')[0] == num_str), None)
        if not target_file:
            messagebox.showerror("错误", f"在当前页面未找到编号为 {num_str} 的文件。")
            return
        if messagebox.askyesno("确认删除", f"您确定要删除文件 '{target_file}' 吗？"):
            os.remove(os.path.join(page_path, target_file))
            renumber_sequentially(page_path)
            self.delete_entry.delete(0, tk.END)
            self.root.after(50, self._on_page_select)
            show_toast(self.root, f"已成功删除文件 '{target_file}', 文件已重新编号")

    def _add_move(self):
        try:
            start = int(self.start_entry.get())
            end = int(self.end_entry.get()) if self.end_entry.get() else start
            dest = int(self.dest_entry.get())
            if not (0 < start <= end and dest > 0):
                raise ValueError
        except ValueError:
            return messagebox.showwarning("警告", "输入无效。请确保为正整数，且起始不大于结束。")
        self.moves.append((start - 1, end - 1, dest - 1))
        self.moves_listbox.insert(tk.END, f"移动块 [{start}-{end}] 到新位置 {dest}")
        for entry in [self.start_entry, self.end_entry, self.dest_entry]:
            entry.delete(0, tk.END)

    def _clear_moves(self):
        self.moves.clear()
        self.moves_listbox.delete(0, tk.END)

    def _execute_all_moves(self):
        page_path = self._get_current_page_path()
        if not page_path or not self.moves:
            return
        if messagebox.askyesno("确认操作", f"您确定要执行这 {len(self.moves)} 条移动指令吗？"):
            reorder_files_by_block_moves(page_path, self.moves)
            self._on_page_select()
            messagebox.showinfo("成功", "所有移动操作已执行完毕！")

    def _to_compare(self):
        folder = self.main_folder_path
        page = self.page_combo.get()

        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("路径无效", "请先提供一个有效的文件夹路径。")
            return
        if not page:
            messagebox.showwarning("页面无效", "请先选择一个有效的页面。")
            return
        if '-' in os.listdir(os.path.join(folder, page))[0]:
            messagebox.showerror("错误", "请先点击自动重命名按钮，确保文件名格式正确。")
            return
        self.root.destroy()
        new_root = tk.Tk()
        Compare(new_root, folder, page)
        new_root.mainloop()

    def _remove_nexist(self):
        col = int(self.column_entry.get())
        row = int(self.row_entry.get())
        if col <= 0 or row <= 0 or not col or not row:
            messagebox.showwarning("警告", "请输入有效的列和行。")
            return
        position = f"{col}_{row}"
        if position not in self.positions:
            messagebox.showwarning("警告", f"位置 {position} 未找到。")
            return
        self.positions.remove(position)
        page_name = self.page_combo.get()
        write_txt(os.path.join(self.main_folder_path, f"{page_name}-position.txt"), self.positions)
        show_toast(self.root, f"已成功移除位置 {position}")

    def _rename_start(self):
        page_name = self.page_combo.get()
        page_path = os.path.join(self.main_folder_path, page_name)
        page_names = sorted(os.listdir(page_path), key=file_sort_key)
        if not page_name:
            messagebox.showerror("错误", "请先选择一个页面！")
            return
        if not self.positions:
            messagebox.showerror("错误", "未找到位置信息文件。")
            return
        for old_name,pos in zip(page_names,self.positions):
            prename, _ = os.path.splitext(old_name)
            character = prename.split('-')[-1]
            page_num = page_name.split('_')[-1]
            new_name = f"_{page_num}_{pos}_{character}.png"
            os.rename(os.path.join(page_path, old_name), os.path.join(page_path, new_name))
        self.root.after(50, self._on_page_select)
        show_toast(self.root, f"重命名成功")
