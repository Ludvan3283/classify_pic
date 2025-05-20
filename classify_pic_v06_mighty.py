import os
import shutil
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk

# 设置最大图像尺寸
MAX_IMAGE_SIZE = (5000, 5000)  # 最大宽度和高度


# 自定义异常类
class ImageTooLargeError(Exception):
    pass


# 显示图片并处理分类的函数
def classify_images(base_path, target_base_path):
    images = [f for f in os.listdir(base_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
    targets = ['有问题', '没有问题']
    error_folder = os.path.join(target_base_path, 'error')  # 出错文件夹路径

    # 创建 tkinter 主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口，避免显示空白窗口

    # 获取屏幕宽度和高度
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 设置窗口大小
    window_width = screen_width
    window_height = screen_height

    current_index = 0  # 当前图像索引
    history = []  # 用于存储已处理图像的历史记录

    # 确保出错文件夹存在
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)

    while current_index < len(images):
        image = images[current_index]
        image_path = os.path.join(base_path, image)

        try:
            with Image.open(image_path) as img:
                if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                    raise ImageTooLargeError(f"图像 {image} 超过最大尺寸限制")  # 抛出自定义异常

                # 创建新的窗口用于显示图片
                image_window = tk.Toplevel(root)
                image_window.title(f"分类图片：{image}")

                # 设置窗口大小和位置
                image_window.geometry(f"{window_width}x{window_height}+0+0")

                # 显示图片
                img.thumbnail((window_width, window_height))  # 调整图片大小以适应窗口
                tk_img = ImageTk.PhotoImage(img)
                label = tk.Label(image_window, image=tk_img)
                label.pack(expand=True)

                # 通过对话框获取用户输入
                category = simpledialog.askinteger(
                    "分类",
                    "按1-2以分类图片 :\n 1:有问题\n 2:没有问题\n 0:退出\n -1:回滚",
                    minvalue=-1, maxvalue=2
                )

                # 处理用户输入
                if category is not None:
                    if category == -1:  # 回滚到上一个图像
                        if history:
                            last_image_path, last_target_folder = history.pop()  # 获取上一个图像的路径和目标文件夹

                            # 将上一个图像移动到目标文件夹
                            shutil.move(last_target_folder, last_image_path)
                            current_index -= 1  # 回滚索引

                        else:
                            messagebox.showinfo("提示", "没有更多的图像可以回滚。")
                    elif 1 <= category <= 2:  # 有效分类
                        target_folder = os.path.join(target_base_path, f'{targets[category - 1]}')

                        target_image_path = os.path.join(target_folder, f'{os.path.basename(image_path)}')

                        if not os.path.exists(target_folder):
                            os.makedirs(target_folder)

                        shutil.move(image_path, os.path.join(target_folder, image))  # 剪切到目标文件夹

                        # 记录当前图像和目标文件夹到历史
                        history.append((image_path, target_image_path))

                        current_index += 1  # 移动到下一个图像
                    elif category == 0:  # 退出程序
                        break

                # 关闭图片窗口
                image_window.destroy()

        except ImageTooLargeError as e:
            messagebox.showwarning("警告", str(e) + "，已移动到出错文件夹。")
            shutil.move(image_path, os.path.join(error_folder, image))  # 剪切到出错文件夹
            continue  # 跳过该图像
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图像 {image}：{e}")
            shutil.move(image_path, os.path.join(error_folder, image))  # 剪切到出错文件夹
            continue  # 跳过该图像

    # 退出 tkinter 主循环
    root.quit()


def prompt_for_paths():
    # 创建一个新的 Tkinter 窗口用于输入路径
    path_window = tk.Tk()
    path_window.title("输入路径")

    # 输入框和标签
    tk.Label(path_window, text="请使用双反斜杠（\\）或正斜杠（/）作为路径分隔符").pack(pady=5)

    tk.Label(path_window, text="输入待筛选图片的路径:").pack(pady=10)
    base_path_entry = tk.Entry(path_window, width=50)
    base_path_entry.pack(pady=10, padx=20)

    tk.Label(path_window, text="输入图片分类的目标路径:").pack(pady=10)
    target_base_path_entry = tk.Entry(path_window, width=50)
    target_base_path_entry.pack(pady=10, padx=20)

    def on_submit():
        base_path = base_path_entry.get()
        target_base_path = target_base_path_entry.get()

        if not os.path.isdir(base_path):
            messagebox.showerror("错误", "找不到待筛选图片的路径")
            return
        if not os.path.isdir(target_base_path):
            messagebox.showerror("错误", "找不到目标路径")
            return

        # 关闭路径输入窗口
        path_window.destroy()

        # 开始分类图像
        classify_images(base_path, target_base_path)

    # 提交按钮
    tk.Button(path_window, text="确认", command=on_submit).pack(pady=20)

    # 启动路径输入窗口的事件循环
    path_window.mainloop()


if __name__ == "__main__":
    prompt_for_paths()
