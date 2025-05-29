import os
import re
import shutil
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import time

MAX_IMAGE_SIZE = (5000, 5000)

class ImageTooLargeError(Exception):
    pass

class NoCancelDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, prompt=None, **kwargs):
        self.prompt = prompt
        super().__init__(parent, title=title, **kwargs)

    def body(self, master):
        tk.Label(master, text=self.prompt).pack(padx=5, pady=5)
        self.entry = tk.Entry(master)
        self.entry.pack(padx=5, pady=5)
        return self.entry

    def validate(self):
        try:
            self.result = int(self.entry.get())
            return 1
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数字")
            return 0

    def buttonbox(self):
        box = tk.Frame(self)
        w = tk.Button(box, text="确定", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        box.pack(pady=5)

# 保存和加载分类信息
def save_categories(categories):
    with open("categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

def load_categories():
    if os.path.exists("categories.json"):
        with open("categories.json", "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


def classify_images(base_path, target_base_path, custom_targets, max_image_size=(5000, 5000)):
    images = [f for f in os.listdir(base_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
    default_targets = ['有问题', '没有问题']
    all_targets = custom_targets if custom_targets else default_targets

    error_folder = os.path.join(target_base_path, 'error')
    os.makedirs(error_folder, exist_ok=True)

    root = tk.Tk()
    root.title("图片分类")

    # 设置为全屏
    root.attributes('-fullscreen', True)

    # 禁止调整窗口大小
    root.resizable(False, False)

    current_index = 0
    history = []
    current_image = None
    tk_img = None

    label = tk.Label(root)
    label.place(x=0, y=0, relwidth=1, relheight=1)

    instructions = (
            "操作说明:\n"
            "需要用英文键盘操作\n"
            "A: 逆时针旋转90度\n"
            "D: 顺时针旋转90度\n"
            "W: 垂直翻转\n"
            "S: 水平翻转\n"
            "\n按数字键分类图片:\n"
            + "\n".join(f"{i}: {target}" for i, target in enumerate(all_targets, 1))
            + "\n\n0: 退出\n-: 回滚上一步"
    )
    instruction_label = tk.Label(
        root, text=instructions, justify=tk.LEFT, font=("Arial", 14),
        bg='#FFFFFF', fg='black', bd=2, relief='solid', padx=10, pady=10, anchor='ne'
    )
    instruction_label.place(relx=1.0, y=20, anchor='ne', x=-20)

    def load_image():
        nonlocal current_image, tk_img, current_index
        if current_index >= len(images):
            messagebox.showinfo("完成", "所有图片已分类完成！")
            root.destroy()
            return
        image_name = images[current_index]
        image_path = os.path.join(base_path, image_name)
        try:
            with Image.open(image_path) as img:
                current_image = img.copy()
                if current_image.width > max_image_size[0] or current_image.height > max_image_size[1]:
                    raise ImageTooLargeError(f"图像 {image_name} 超过最大尺寸限制")
                display_img = current_image.copy()
                tk_img = ImageTk.PhotoImage(display_img)
                label.config(image=tk_img)
                root.title(f"分类图片：{image_name}  ({current_index + 1}/{len(images)})")
        except ImageTooLargeError as e:
            messagebox.showwarning("警告", str(e) + "，已移动到错误文件夹。")
            shutil.move(image_path, os.path.join(error_folder, image_name))
            images.pop(current_index)
            load_image()
            return
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图像 {image_name}：{e}，已移动到错误文件夹。")
            shutil.move(image_path, os.path.join(error_folder, image_name))
            images.pop(current_index)
            load_image()
            return
        return True

    def update_image():
        nonlocal tk_img
        if current_image is not None:
            display_img = current_image.copy()
            tk_img = ImageTk.PhotoImage(display_img)
            label.config(image=tk_img)

    def rotate_image(direction):
        nonlocal current_image
        if current_image is not None:
            if direction == 'left':
                current_image = current_image.rotate(90, expand=True)
            elif direction == 'right':
                current_image = current_image.rotate(-90, expand=True)
            update_image()

    def flip_image(axis):
        nonlocal current_image
        if current_image is not None:
            if axis == 'vertical':
                current_image = current_image.transpose(Image.FLIP_TOP_BOTTOM)
            elif axis == 'horizontal':
                current_image = current_image.transpose(Image.FLIP_LEFT_RIGHT)
            update_image()

    def key_press(event):
        nonlocal current_index, current_image
        key = event.char
        lt = len(all_targets)
        if current_index >= len(images):
            return
        image_name = images[current_index]
        image_path = os.path.join(base_path, image_name)

        if key in '123456789':
            idx = int(key)
            if 1 <= idx <= lt:
                target_folder = os.path.join(target_base_path, all_targets[idx - 1])
                os.makedirs(target_folder, exist_ok=True)
                save_path = os.path.join(target_folder, image_name)
                try:
                    if current_image is not None:
                        current_image.save(save_path)
                    os.remove(image_path)
                    history.append((image_path, save_path, current_image.copy()))
                    images.pop(current_index)
                    load_image()
                except Exception as e:
                    messagebox.showerror("错误", f"保存图片失败: {e}")
        elif key == '0':
            if messagebox.askyesno("退出", "确认退出分类吗？"):
                root.destroy()
        elif key == '-':
            if history:
                last_image_path, last_save_path, last_img = history.pop()
                shutil.move(last_save_path, last_image_path)
                images.insert(current_index, os.path.basename(last_image_path))
                current_image = last_img
                update_image()
            else:
                messagebox.showinfo("提示", "没有更多图片可以回滚。")
        elif key == 'a':
            rotate_image('left')
        elif key == 'd':
            rotate_image('right')
        elif key == 'w':
            flip_image('vertical')
        elif key == 's':
            flip_image('horizontal')

    root.bind("<Key>", key_press)
    load_image()
    root.mainloop()
    save_categories(all_targets)

def fade_in(window):
    for i in range(11):
        window.attributes("-alpha", i * 0.1)  # 设置透明度
        window.update()
        time.sleep(0.05)  # 控制渐变速度

def center_window(window, width, height):
    # 获取屏幕宽度和高度
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # 计算居中位置
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # 设置窗口位置
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_info_dialog():
    info_dialog_width = 500
    info_dialog_height = 400

    info_dialog = tk.Toplevel()
    info_dialog.title("")
    info_dialog.geometry(f"{info_dialog_width}x{info_dialog_height}")
    info_dialog.resizable(False, False)
    center_window(info_dialog, info_dialog_width, info_dialog_height)

    info_label = tk.Label(info_dialog, text="链接：https://github.com/Ludvan3283/classify_pic", font=("Arial", 10))
    info_label.pack(pady=20)

    # 加载并调整图片大小
    image_path = r".\icon\vergil.jpg"  # 替换为您的图片路径
    original_image = Image.open(image_path)
    resized_image = original_image.resize(
        (info_dialog_width, int(info_dialog_width * original_image.height / original_image.width)), Image.LANCZOS)
    photo = ImageTk.PhotoImage(resized_image)

    # 在对话框中显示图片
    image_label = tk.Label(info_dialog, image=photo)
    image_label.image = photo  # 保持对图片的引用
    image_label.pack(pady=10)

    def close_dialog():
        info_dialog.destroy()

    close_button = tk.Button(info_dialog, text="返回", command=close_dialog)
    close_button.pack(pady=5)

def prompt_for_paths():
    path_window = tk.Tk()
    path_window.title("输入路径和分类")
    path_window.geometry("400x500")  # 设置固定大小
    path_window.resizable(False, False)  # 禁止调整窗口大小
    path_window.attributes("-alpha", 0)  # 初始透明度为0
    center_window(path_window, 400, 500)

    tk.Label(path_window, text="请使用双反斜杠（\\\\）或正斜杠（/）作为路径分隔符").pack(pady=5)
    tk.Label(path_window, text="输入待筛选图片的路径:").pack(pady=10)
    base_path_entry = tk.Entry(path_window, width=50)
    base_path_entry.pack(pady=10, padx=20)

    tk.Label(path_window, text="输入图片分类的目标路径:").pack(pady=10)
    target_base_path_entry = tk.Entry(path_window, width=50)
    target_base_path_entry.pack(pady=10, padx=20)

    # 新增：图片最大大小输入框
    tk.Label(path_window, text="图片最大宽高（格式：宽,高）:").pack(pady=10)
    tk.Label(path_window, text="中英文逗号均可").pack(pady=2)
    max_size_entry = tk.Entry(path_window, width=20)
    max_size_entry.pack(pady=10, padx=20)
    max_size_entry.insert(0, f"{MAX_IMAGE_SIZE[0]},{MAX_IMAGE_SIZE[1]}")

    saved_categories = load_categories()
    tk.Label(path_window, text="自定义分类(多个分类用逗号（中、英均可）分隔，留空则使用默认分类):").pack(pady=10)
    tk.Label(path_window, text="默认：有问题，没有问题").pack(pady=2)
    custom_categories_entry = tk.Entry(path_window, width=50)
    custom_categories_entry.pack(pady=10, padx=20)

    if saved_categories:
        custom_categories_entry.insert(0, ','.join(saved_categories))

    # 在左下角添加文本并绑定点击事件
    info_label = tk.Label(path_window, text="源码链接", fg="blue", cursor="hand2")
    info_label.pack(side=tk.BOTTOM, anchor='sw', padx=10, pady=10)
    info_label.bind("<Button-1>", lambda e: show_info_dialog())


    def on_submit():
        base_path = base_path_entry.get()
        target_base_path = target_base_path_entry.get()

        # 获取最大图片大小
        max_size_str = max_size_entry.get().strip()
        try:
            max_size_str = re.sub(r'[，,]', ',', max_size_str)

            width, height = map(int, max_size_str.split(','))
            max_image_size = (width, height)
        except Exception:
            messagebox.showerror("错误", "图片最大宽高格式错误，应为：宽,高（如 5000,5000）")
            return

        custom_categories = custom_categories_entry.get().strip()
        custom_targets = [cat.strip() for cat in re.split('[,，]', custom_categories) if cat.strip()] if custom_categories else []

        if not os.path.isdir(base_path):
            messagebox.showerror("错误", "找不到待筛选图片的路径")
            return
        if not os.path.isdir(target_base_path):
            messagebox.showerror("错误", "找不到目标路径")
            return

        path_window.destroy()
        classify_images(base_path, target_base_path, custom_targets, max_image_size)

    tk.Button(path_window, text="确认", command=on_submit).pack(pady=20)

    # 渐变效果
    fade_in(path_window)

    path_window.mainloop()

if __name__ == "__main__":
    prompt_for_paths()
