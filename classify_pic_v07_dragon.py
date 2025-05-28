import os
import re
import shutil
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk

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
        box.pack()

# 保存和加载分类信息（每组分类为一个数组，所有组为一个大数组）
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

def classify_images(base_path, target_base_path, custom_targets):
    images = [f for f in os.listdir(base_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
    default_targets = ['有问题', '没有问题']
    all_targets = custom_targets if custom_targets else default_targets

    error_folder = os.path.join(target_base_path, 'error')
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)

    root = tk.Tk()
    root.withdraw()

    current_index = 0
    history = []

    while current_index < len(images):
        image = images[current_index]
        image_path = os.path.join(base_path, image)

        try:
            with Image.open(image_path) as img:
                if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                    raise ImageTooLargeError(f"图像 {image} 超过最大尺寸限制")

                image_window = tk.Toplevel(root)
                image_window.title(f"分类图片：{image}")
                image_window.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

                img.thumbnail((root.winfo_screenwidth(), root.winfo_screenheight()))
                tk_img = ImageTk.PhotoImage(img)
                label = tk.Label(image_window, image=tk_img)
                label.pack(expand=True)

                prompt_text = "按数字键分类图片:\n" + "\n".join(f"{i}: {target}" for i, target in enumerate(all_targets, 1))
                prompt_text += "\n\n0: 退出\n-1: 回滚"

                dialog = NoCancelDialog(image_window, title="分类", prompt=prompt_text)

                category = getattr(dialog, 'result', None)
                if category is None:
                    category = 0

                lt = len(all_targets)

                if category == -1:
                    if history:
                        last_image_path, last_target_folder = history.pop()
                        shutil.move(last_target_folder, last_image_path)
                        current_index -= 1
                    else:
                        messagebox.showinfo("提示", "没有更多的图像可以回滚。")
                elif 1 <= category <= lt:
                    target_folder = os.path.join(target_base_path, all_targets[category - 1])
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)

                    shutil.move(image_path, os.path.join(target_folder, image))
                    history.append((image_path, os.path.join(target_folder, image)))
                    current_index += 1
                elif category > lt:
                    messagebox.showinfo("提示", "输入值有误，请重新输入")
                elif category == 0:
                    break

                image_window.destroy()

        except ImageTooLargeError as e:
            messagebox.showwarning("警告", str(e) + "，已移动到出错文件夹。")
            shutil.move(image_path, os.path.join(error_folder, image))
            continue
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图像 {image}：{e}")
            shutil.move(image_path, os.path.join(error_folder, image))
            continue

    root.quit()
    # 保存本次分类
    save_categories(all_targets)

def prompt_for_paths():
    path_window = tk.Tk()
    path_window.title("输入路径和分类")

    tk.Label(path_window, text="请使用双反斜杠（\\）或正斜杠（/）作为路径分隔符").pack(pady=5)
    tk.Label(path_window, text="输入待筛选图片的路径:").pack(pady=10)
    base_path_entry = tk.Entry(path_window, width=50)
    base_path_entry.pack(pady=10, padx=20)

    tk.Label(path_window, text="输入图片分类的目标路径:").pack(pady=10)
    target_base_path_entry = tk.Entry(path_window, width=50)
    target_base_path_entry.pack(pady=10, padx=20)

    # 只加载最新一组分类
    saved_categories = load_categories()
    tk.Label(path_window, text="自定义分类(多个分类用逗号分隔，留空则使用默认分类):").pack(pady=10)
    custom_categories_entry = tk.Entry(path_window, width=50)
    custom_categories_entry.pack(pady=10, padx=20)

    # 自动填充
    if saved_categories:
        custom_categories_entry.insert(0, ','.join(saved_categories))

    def on_submit():
        base_path = base_path_entry.get()
        target_base_path = target_base_path_entry.get()

        custom_categories = custom_categories_entry.get().strip()
        custom_targets = [cat.strip() for cat in re.split('[,，]', custom_categories) if cat.strip()] if custom_categories else []

        if not os.path.isdir(base_path):
            messagebox.showerror("错误", "找不到待筛选图片的路径")
            return
        if not os.path.isdir(target_base_path):
            messagebox.showerror("错误", "找不到目标路径")
            return

        path_window.destroy()
        classify_images(base_path, target_base_path, custom_targets)

    tk.Button(path_window, text="确认", command=on_submit).pack(pady=20)
    path_window.mainloop()


if __name__ == "__main__":
    prompt_for_paths()
