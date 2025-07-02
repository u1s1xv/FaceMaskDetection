import cv2

# 文件路径
image_path = 'E:\GitCloneProject\FaceMaskDetection\yoloserver\data\crawled\images\mask_weared_incorrect_026dee7d42890927dfc72803ab8714d1.jpg'
label_path = 'E:\GitCloneProject\FaceMaskDetection\yoloserver\data\crawled\images\mask_weared_incorrect_026dee7d42890927dfc72803ab8714d1.jpg'

# 读取图像
image = cv2.imread(image_path)
height, width, _ = image.shape

# 读取标签并绘制框
with open(label_path, 'r') as f:
    for line in f:
        class_id, x_center, y_center, w, h = map(float, line.strip().split())

        # 转换为图像坐标
        x_center *= width
        y_center *= height
        w *= width
        h *= height

        x1 = int(x_center - w / 2)
        y1 = int(y_center - h / 2)
        x2 = int(x_center + w / 2)
        y2 = int(y_center + h / 2)

        # 绘制矩形框和类标
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, f"Class {int(class_id)}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# 显示图像
cv2.imshow("YOLO Bounding Boxes", image)
cv2.waitKey(0)
cv2.destroyAllWindows()

