import os
import shutil
from PIL import Image, ImageTk
import tkinter as tk

#流程为将图片全屏显示后再向pycharm控制台输入数字以控制图片的保存位置，缺点是只能按esc键退出图片全屏浏览才能进行下一步操作

def show_image_fullscreen(image_path):
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    img = Image.open(image_path)
    tk_img = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=tk_img)
    label.pack()

    def close():
        root.destroy()

    root.after(100, root.focus_force)  # Ensure the window gets focus
    root.after(100, lambda: root.bind('<Escape>', lambda e: close()))  # Allow closing with Escape key
    root.mainloop()

def classify_images(base_path):
    images = [f for f in os.listdir(base_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
    targets = ['非文档', '合同', '黑底白字', '红头文件', '书籍', '文档', '不好区分的']
    for image in images:
        image_path = os.path.join(base_path, image)

        while True:
            try:
                show_image_fullscreen(image_path)

                category = int(input("按1-7以分类图片 :\n 1:非文档\n 2:合同\n 3:黑底白字\n 4:红头文件\n 5:书籍\n 6:文档\n 7:不好区分的\n 0:退出\n"))
                if 1 <= category <= 7:
                    target_folder = os.path.join(base_path, f'{targets[category-1]}')  # 修改为其他路径

                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(image_path, target_folder)
                    break
                elif category == 0:
                    quit()
                else:
                    print("请按1-7 ")
            except ValueError:
                print("不合法的值，请按1-7 ")

def main():
    base_path = input("输入待筛选图片的路径: ")
    if not os.path.isdir(base_path):
        print("找不到该路径")
        return

    classify_images(base_path)

if __name__ == "__main__":
    main()
