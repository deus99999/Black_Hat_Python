"""Создаваемая нами служба имитирует ряд уязвимостей, которые часто встречаются в крупных корпоративных сетях. Позже в
этой главе мы ее атакуем. Эта служба будет периодически копировать скрипт во временную папку и запускать его оттуда.


Это каркас тех функций, которые должна предоставлять любая служба. Данный класс наследует win32serviceutil.ServiceFramework и определяет три
Создание уязвимой хакерской службы  191
метода. В методе __init__ мы инициализируем ServiceFramework, определяем
местоположение скрипта, который нужно запустить, устанавливаем время
ожидания длиной в 1 минуту и создаем объект события . """

import os
import servicemanager
import shutil
import subprocess
import sys

import win32event
import win32service
import win32serviceutil

# устанавливаем исходный каталог для файла скрипта и затем выбираем целевой каталог, из которого он будет запущен службой
SRDIR = 'bhservice_task.vbs'
TGTDIR = 'C:\\Windows\\TEMP'


class BHServerRvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "BlackHatService"
    _svc_display_name_ = "Black Hat Service"
    _svc_description_ = ("Executes VBScripts at regular intervals." + "What could possible go wrong?")

    def __init__(self, args):
        self.vbs = os.path.join(TGTDIR, 'bhservice_task.vbs')
        self.timeout = 1000 * 60

        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        """В методе SvcStop указываем состояние службы и останавливаем его выполнение"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        """В методе SvcDoRun запускаем службу и вызываем метод main, в котором будут работать наши задания"""
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()

    def main(self):
        """инициируем цикл, который выполняется раз в минуту (в соответствии с параметром self.timeout), пока служба не
        получит сигнал остановки. В ходе выполнения копируем скрипт в целевой каталог, выполняем его и удаляем файл """
        while True:
            ret_code = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            if ret_code == win32event.WAIT_OBJECT_0:
                servicemanager.LogInfoMsg("Service is stopping")
                break
            src = os.path.join(SRDIR, 'bhservice_task.vbs')
            shutil.copy(src, self.vbs)
            subprocess.call('cscript.exe %s' % self.vbs, shell=False)
            os.unlink(self.vbs)


"""В главном блоке мы обрабатываем все аргументы командной строки"""
if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BHServerRvc)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(BHServerRvc)