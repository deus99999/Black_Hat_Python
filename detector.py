import cv2
import os

# ROOT = '/root/Desktop/pictures'
# FACES = 'root/Desktop/faces'
# TRAIN = '/root/Desktop/training'

ROOT = '/pictures'
FACES = '/faces'
TRAIN = '/training'


def detect(srcdir=ROOT, tgtdir=FACES, train_dir=TRAIN):
    """Функция detect перебирает каждый файл JPG в исходной папке (мы ищем лица, поэтому изображения, предположительно,
     являются фотографиями и, скорее всего, хранятся в файлах с расширением .jpg ). Затем считываем изображение с
     помощью библиотеки компьютерного зрения OpenCV, cv2 , загружаем XML-файл detector и создаем объект cv2 для
     обнаружения лиц. Этот объект является классификатором, заранее обученным находить лица, запечатленные анфас.
     Обнаружив лицо, классификатор возвращает координаты соответствующей прямоугольной области на изображении.
     В этом случае мы выводим сообщение в консоль, рисуем зеленую рамку вокруг лица  и записываем изображение в
     выходной каталог."""
    for fname in os.listdir(srcdir):
        if not fname.upper().endswith('.JPG'):
            continue
        fullname = os.path.join(srcdir, fname)
        newname = os.path.join(tgtdir, fname)
        img = cv2.imread(fullname)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        training = os.path.join(train_dir, 'haarcascade_frontalface_alt.xml')
        cascade = cv2.CascadeClassifier(training)
        rects = cascade.detectMultiScale(gray, 1.3, 5)
        try:
            if rects.any():
                print('Got a face')
                rects[:, 2:] += rects[:, :2]
        except AttributeError:
            print(f'No faces found in {fname}')
            continue

        # выделение лиц на изображении
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), (127, 255, 0), 2)
        cv2.imwrite(newname, img)


if __name__ == '__main__':
    detect()
