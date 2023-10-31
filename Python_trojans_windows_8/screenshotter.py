import base64
import win32api
import win32con
import win32gui
import win32ui


def get_dimensions():
    """определяем размер экрана (или экранов), чтобы знать, насколько большим должен быть наш снимок."""
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    return (width, height, left, top)


def screenshot(name='screenshot'):
    hdesktop = win32gui.GetDesktopWindow()  # дескриптор всего рабочего стола, который охватывает все видимое пространство на всех мониторах
    width, height, left, top = get_dimensions()

    desktop_dc = win32gui.GetWindowDC(hdesktop)  # Создаем контекст устройства с помощью функции GetWindowDC и передаем дескриптор рабочего стола
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()  # создаем контекст устройства в памяти, в котором будут храниться байты захваченного растрового изображения, пока мы не запишем их в файл.

    screenshot = win32ui.CreateBitmap() # создаем объект растрового изображения, привязанный к контексту устройства нашего рабочего стола
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)  # Вызов SelectObject делает так, чтобы контекст устройства в памяти
    # указывал на объект захватываемого растрового изображения. Мы используем функцию BitBlt , чтобы создать точную копию того, что изображено на
    # экране, и сохранить ее в контекст в памяти.
    screenshot.SaveBitmapFile(mem_dc, f'{name}.bmp')  # сбрасываем данный снимок на диск

    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())


def run():
    screenshot()
    with open('screenshot.bmp') as f:
        img = f.read()
    return img


if __name__ == '__main__':
    screenshot()