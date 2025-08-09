import re
import os
import tkinter as tk
from tkinter import messagebox

def center_window(window, width_ratio=0.7, height_ratio=0.7):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    app_width = int(screen_width * width_ratio)
    app_height = int(screen_height * height_ratio)
    center_x = int((screen_width - app_width) / 2)
    center_y = int((screen_height - app_height) / 2)
    window.geometry(f'{app_width}x{app_height}+{center_x}+{center_y}')
    window.minsize(int(app_width * 0.8), int(app_height * 0.8))  # 设置最小尺寸

def read_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

def write_txt(txt_path, pos_lst):
    with open(txt_path, 'w', encoding='utf-8') as f:
        for pos in pos_lst:
            f.write(f"{pos}\n")

def sort_file(filename):
    # 找出所有数字
    nums = re.findall(r'(\d+)', filename)
    if len(nums) >= 2:
        # 根据倒数第二个和倒数第一个数字排序
        return int(nums[-2]), int(nums[-1])
    elif len(nums) == 1:
        return int(nums[-1]), 0
    else:
        return 0, 0

def file_sort_key(file_name):
    """从文件名中提取前导数字用于排序。"""
    nums = re.findall(r'^\d+', file_name)
    return int(nums[0]) if nums else 0

def _safe_rename_files(page_path, final_file_order):
    temp_files = []
    files_to_rename = set(os.listdir(page_path))

    for i, file_name in enumerate(final_file_order):
        if file_name in files_to_rename:
            temp_name = f"_temp_{i}_{file_name}"
            os.rename(os.path.join(page_path, file_name), os.path.join(page_path, temp_name))
            temp_files.append(temp_name)

    for i, temp_name in enumerate(temp_files):
        try:
            _, _, original_full_name = temp_name.split('_', 2)
            _, descriptive_part_with_ext = original_full_name.split('-', 1)
            new_name = f"{i + 1}-{descriptive_part_with_ext}"
            os.rename(os.path.join(page_path, temp_name), os.path.join(page_path, new_name))
        except (ValueError, IndexError):
            print(f"警告：无法解析临时文件名 '{temp_name}'。该文件可能未被正确重命名。")
            continue

def renumber_sequentially(page_path):
    """删除文件后，按顺序重新编号所有文件。"""
    try:
        files = sorted(os.listdir(page_path), key=file_sort_key)
        _safe_rename_files(page_path, files)
        print("顺序重新编号完成。")
    except Exception as e:
        print(f"在重新编号过程中发生错误: {e}")

def reorder_files_by_block_moves(page_path, moves):
    try:
        initial_files = sorted(os.listdir(page_path), key=file_sort_key)
        n = len(initial_files)
        if not n:
            return

        final_order_blueprint = [None] * n
        moved_source_indices = set()
        moved_target_indices = set()

        for start, end, dest in moves:
            for block_offset in range(end - start + 1):
                source_index = start + block_offset
                dest_index = dest + block_offset

                # 安全检查
                if not (0 <= source_index < n and 0 <= dest_index < n):
                    print(f"警告：指令导致索引越界。源索引: {source_index + 1}, 目标索引: {dest_index + 1}。已跳过此条目。")
                    continue
                if dest_index in moved_target_indices:
                    print(f"警告：目标位置 {dest_index + 1} 已被其他指令占用。已跳过对该位置的赋值。")
                    continue

                # 执行精确映射：将原始文件放入蓝图的指定位置
                final_order_blueprint[dest_index] = initial_files[source_index]
                moved_source_indices.add(source_index)
                moved_target_indices.add(dest_index)

        unmoved_files = []
        for i, f in enumerate(initial_files):
            if i not in moved_source_indices:
                unmoved_files.append(f)

        unmoved_iter = iter(unmoved_files)
        for i in range(n):
            if final_order_blueprint[i] is None:
                try:
                    final_order_blueprint[i] = next(unmoved_iter)
                except StopIteration:
                    messagebox.showerror("严重错误", "文件重排逻辑错误：剩余空位与未移动文件数不匹配。操作已取消。")
                    return

        if len(final_order_blueprint) != n or any(f is None for f in final_order_blueprint):
            messagebox.showerror("严重错误", "文件重排后数量不匹配或存在空位，操作已取消以防数据损坏。")
            return

        _safe_rename_files(page_path, final_order_blueprint)
        print("批量重新排序完成。")
    except (IOError, OSError, ValueError) as e:
        messagebox.showerror("重排错误", f"在批量重排时发生意外错误: {e}")

def show_toast(master, text, duration=2000, fade_steps=10):
    class Toast(tk.Toplevel):
        def __init__(self, master, text, duration, fade_steps):
            super().__init__(master)
            self.duration = duration
            self.fade_steps = fade_steps
            self.fade_delay = 50

            self.overrideredirect(True)
            self.attributes('-topmost', True)
            self.attributes('-alpha', 0)

            label = tk.Label(self, text=text, bg="#333", fg="white",
                             font=("Arial", 12), padx=15, pady=8)
            label.pack()

            self.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_y() + 50
            self.geometry(f"+{x}+{y}")

            self.after(0, self.fade_in)

        def fade_in(self, step=0):
            alpha = step / self.fade_steps
            self.attributes('-alpha', alpha)
            if step < self.fade_steps:
                self.after(self.fade_delay, self.fade_in, step + 1)
            else:
                self.after(self.duration, self.fade_out)

        def fade_out(self, step=None):
            if step is None:
                step = self.fade_steps
            alpha = step / self.fade_steps
            self.attributes('-alpha', alpha)
            if step > 0:
                self.after(self.fade_delay, self.fade_out, step - 1)
            else:
                self.destroy()

    Toast(master, text, duration, fade_steps)

