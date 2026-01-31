import re

def center_window(window, width_ratio=0.7, height_ratio=0.7):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    app_width = int(screen_width * width_ratio)
    app_height = int(screen_height * height_ratio)
    center_x = int((screen_width - app_width) / 2)
    center_y = int((screen_height - app_height) / 2)
    window.geometry(f'{app_width}x{app_height}+{center_x}+{center_y}')
    window.minsize(int(app_width * 0.8), int(app_height * 0.8))  # 设置最小尺寸

def file_sort_key(file_name):
    """从文件名中提取前导数字用于排序。"""
    nums = re.findall(r'\d+', file_name)
    return int(nums[0]) if nums else 0