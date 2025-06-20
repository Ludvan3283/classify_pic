import os
import re
import shutil
import json
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import time

MAX_IMAGE_SIZE = (5000, 5000)

DISPLAY_SIZE = (900, 900)  # 固定的显示尺寸


# 自定义异常
class ImageTooLargeError(Exception):
    pass


# 自定义对话框
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


# 类别管理功能
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


# 图像分类功能
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
    key_buffer = ''

    label = tk.Label(root)
    label.place(x=0, y=0, relwidth=1, relheight=1)

    instructions = (
            "操作说明:\n"
            "需要用英文键盘操作\n"
            "A: 逆时针旋转90度\n"
            "D: 顺时针旋转90度\n"
            "W: 垂直翻转\n"
            "S: 水平翻转\n"
            "\n分类图片:\n"
            "输入数字(1-{})后按空格或回车确认\n".format(len(all_targets))
            + "\n".join(f"{i}: {target}" for i, target in enumerate(all_targets, 1))
            + "\n\n0: 退出\n-: 回滚上一步\n退格键: 删除输入的数字"
    )
    instruction_label = tk.Label(
        root, text=instructions, justify=tk.LEFT, font=("Arial", 14),
        bg='#FFFFFF', fg='black', bd=2, relief='solid', padx=10, pady=10, anchor='ne'
    )
    instruction_label.place(relx=1.0, y=20, anchor='ne', x=-20)

    # 图像处理功能
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

                # 保持原始图像不变，仅调整显示大小
                display_img = current_image.copy()
                display_img.thumbnail(DISPLAY_SIZE, Image.LANCZOS)
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
            display_img.thumbnail(DISPLAY_SIZE, Image.LANCZOS)
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

    # 在创建instruction_label之后添加输入显示标签
    input_display = tk.Label(
        root, text="输入: ", font=("Arial", 20),
        bg='white', fg='black', bd=2, relief='solid'
    )
    input_display.place(relx=0.5, y=50, anchor='n', x=-20, rely=0)

    # 修改key_press函数如下：
    def key_press(event):
        nonlocal current_index, current_image, key_buffer
        key = event.char
        lt = len(all_targets)

        # 更新输入显示
        def update_display():
            input_display.config(text=f"输入: {key_buffer}")

        # 0键直接退出（放在最前面处理）
        if key == '0':
            if messagebox.askyesno("退出", "确认退出分类吗？"):
                root.destroy()
            return

        if current_index >= len(images):
            return

        image_name = images[current_index]
        image_path = os.path.join(base_path, image_name)

        # 处理数字输入
        if key.isdigit():
            key_buffer += key
            update_display()
            return

        # 处理确认键（空格或回车）
        if key in (' ', '\r') and key_buffer:
            try:
                idx = int(key_buffer)
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
                        key_buffer = ''
                        update_display()
                        load_image()
                    except Exception as e:
                        messagebox.showerror("错误", f"保存图片失败: {e}")
                else:
                    messagebox.showerror("错误", f"请输入1-{lt}范围内的数字")
                    key_buffer = ''
                    update_display()
            except ValueError:
                messagebox.showerror("错误", "无效的数字输入")
                key_buffer = ''
                update_display()
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
        elif key == '\x08':  # 退格键
            key_buffer = key_buffer[:-1]
            update_display()

    root.bind("<Key>", key_press)
    load_image()
    root.mainloop()
    save_categories(all_targets)


# 用户界面相关功能
def fade_in(window):
    for i in range(11):
        window.attributes("-alpha", i * 0.1)  # 设置透明度
        window.update()
        time.sleep(0.01)  # 控制渐变速度


# 居中窗口
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


# 获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# 另一个对话框，显示源码链接
def show_info_dialog(image_path):
    info_dialog_width = 500
    info_dialog_height = 400

    info_dialog = tk.Toplevel()
    info_dialog.title("")
    info_dialog.geometry(f"{info_dialog_width}x{info_dialog_height}")
    info_dialog.resizable(False, False)
    center_window(info_dialog, info_dialog_width, info_dialog_height)

    info_label = tk.Label(info_dialog, text="链接：https://github.com/Ludvan3283/classify_pic", font=("Arial", 10))
    info_label.pack(pady=20)

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


# 输入路径和类别的对话框
def prompt_for_paths():
    path_window = tk.Tk()
    path_window.title("输入路径和分类")
    path_window.geometry("400x500")  # 设置固定大小
    path_window.resizable(False, False)  # 禁止调整窗口大小
    path_window.attributes("-alpha", 0)  # 初始透明度为0

    # 加载并调整图片大小
    image_path = resource_path('icon\\vergil.jpg')  # 替换为您的图片路径

    center_window(path_window, 400, 500)

    tk.Label(path_window, text="请使用双反斜杠（\\\\）或正斜杠（/）作为路径分隔符").pack(pady=5)
    tk.Label(path_window, text="输入待筛选图片的路径:").pack(pady=5)
    base_path_entry = tk.Entry(path_window, width=50)
    base_path_entry.pack(pady=10, padx=20)

    tk.Label(path_window, text="输入图片分类的目标路径:").pack(pady=5)
    target_base_path_entry = tk.Entry(path_window, width=50)
    target_base_path_entry.pack(pady=10, padx=20)

    # 新增：图片最大大小输入框
    tk.Label(path_window, text="图片最大宽高（格式：宽,高）:\n中英文逗号均可").pack(pady=5)
    max_size_entry = tk.Entry(path_window, width=20)
    max_size_entry.pack(pady=10, padx=20)
    max_size_entry.insert(0, f"{MAX_IMAGE_SIZE[0]},{MAX_IMAGE_SIZE[1]}")

    saved_categories = load_categories()
    tk.Label(path_window,
             text="自定义分类(多个分类用逗号（中、英均可）分隔，留空则使用默认分类)\n默认：有问题，没有问题:").pack(pady=5)
    custom_categories_entry = tk.Entry(path_window, width=50)
    custom_categories_entry.pack(pady=10, padx=20)

    if saved_categories:
        custom_categories_entry.insert(0, ','.join(saved_categories))

    # 在左下角添加文本并绑定点击事件
    info_label = tk.Label(path_window, text="源码链接", fg="blue", cursor="hand2")
    info_label.pack(side=tk.BOTTOM, anchor='sw', padx=10, pady=5)
    info_label.bind("<Button-1>", lambda e: show_info_dialog(image_path))

    # 提交路径与类别
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
        custom_targets = [cat.strip() for cat in re.split('[,，]', custom_categories) if
                          cat.strip()] if custom_categories else []

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