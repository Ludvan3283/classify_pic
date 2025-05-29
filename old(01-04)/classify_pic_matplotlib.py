import os
import shutil
import tkinter as tk
from tkinter import simpledialog

from PIL import Image, ImageTk


#流程为打开一个图片窗口一个对话框，在对对话框进行输入数字时还能同时查看图片，缺点是没有回滚机制以及容易聚焦到别的应用

# 显示图片并处理分类的函数
def classify_images(base_path, target_base_path):
    images = [f for f in os.listdir(base_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
    #'非文档', '合同', '黑底白字', '红头文件', '书籍', '文档', '不好区分的'
    #'数学（有问题）','数学（没有问题）','非数学'
    #'语文（有问题）','语文（没有问题）','非语文'

    targets = ['有问题','没有问题']#

    # 创建 tkinter 主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口，避免显示空白窗口

    # 获取屏幕宽度和高度
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 设置窗口大小
    window_width = screen_width
    window_height = screen_height

    for image in images:
        image_path = os.path.join(base_path, image)

        # 创建新的窗口用于显示图片

        image_window = tk.Toplevel(root)
        image_window.title(f"分类图片：{image}")

        # 设置窗口大小和位置
        image_window.geometry(f"{window_width}x{window_height}+0+0")

        # 显示图片
        img = Image.open(image_path)
        img.thumbnail((window_width, window_height))  # 调整图片大小以适应窗口
        tk_img = ImageTk.PhotoImage(img)
        label = tk.Label(image_window, image=tk_img)
        label.pack(expand=True)

        # 通过对话框获取用户输入
        category = simpledialog.askinteger(
            "分类",
            "按1-2以分类图片 :\n 1:有问题\n 2:没有问题\n 0:退出",#
            minvalue=0, maxvalue=2
        )

        # 如果用户选择了有效的分类，移动图片到目标文件夹
        if category is not None:
            if 1 <= category <= 2:#
                target_folder = os.path.join(target_base_path, f'{targets[category - 1]}')

                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)

                shutil.move(image_path, target_folder)

            elif category == 0:
                root.quit()  # 退出程序
                break

        # 关闭图片窗口
        image_window.destroy()

    # 退出 tkinter 主循环
    root.quit()

#C:\Users\WPS\Desktop\语文
#C:\Users\WPS\Desktop\unichart-table-data_2

#C:\Users\WPS\Desktop\筛选后

def main():
    base_path = input("输入待筛选图片的路径: ")
    if not os.path.isdir(base_path):
        print("找不到该路径")
        return

    target_base_path = input("输入图片分类的目标路径: ")
    if not os.path.isdir(target_base_path):
        print("找不到目标路径")
        return

    classify_images(base_path, target_base_path)

if __name__ == "__main__":
    main()

