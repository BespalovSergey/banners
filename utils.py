from queue import Queue
import cv2


def show_image(image_path: str, q: Queue):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (512, 512))
    window_name = "banner image"
    cv2.imshow(window_name, img)
    while True:
        try:
            q.get(block=False)
        except Exception:
            cv2.waitKey(1000)
        else:
            break
    cv2.destroyAllWindows()
