import os
import shutil
from PIL import Image
#流程为使用数字键对pycharm自带的控制台控制图片的保存位置，缺点是图片一经打开就不能被关闭

#需加入关闭浏览图片窗口函数，以及试图让其全屏显示

def classify_images(base_path):
    images = [f for f in os.listdir(base_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
    targets = ['非文档','合同','黑底白字','红头文件','书籍','文档','不好区分的']
    for image in images:
        image_path = os.path.join(base_path, image)



        while True:
            try:
                img = Image.open(image_path)
                img.show()

                category = int(input("按1-7以分类图片 :\n 1:非文档\n 2:合同\n 3:黑底白字\n 4:红头文件\n 5:书籍\n 6:文档\n 7:不好区分的\n 0:退出\n"))
                if 1 <= category <= 7:
                    target_folder = os.path.join(base_path, f'{targets[category-1]}') #修改为其他路径

                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(image_path, target_folder)
                    img.close()
                    break
                elif category == 0:
                    img.close()
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