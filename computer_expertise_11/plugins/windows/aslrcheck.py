# Ищем все процессы и проверяем наличие защиты ASLR
from typing import Callable, List

from volatility.framework import constants, exceptions, interfaces, renderers
from volatility.framework.configuration import requirements
from volatility.framework.renderers import format_hints
from volatility.framework.symbols import intermed
from volatility.framework.symbols.windows import extensions
from volatility.plugins.windows import pslist

import io
import logging
import os
import pefile

vollog = logging.getLogger(__name__)

IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE = 0x0040
IMAGE_FILE_RELOCS_STRIPPED = 0x0001


def check_aslr(pe):
    """Мы передаем объект PE-файла функции check_aslr , разбираем его и смотрим, был ли он скомпилирован с параметром
    /DYNAMICBASE  и была ли удалена из файла информация о перемещении адресов . Если PE-файл не является динамическим
     или не содержит данных о переносе адресов, это означает, что он не защищен с помощью ASLR"""
    pe.parse_data_directories([
        pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG']
    ])
    dynamic = False
    stripped = False

    if (pe.OPTIONAL_HEADER.DllCharecteristics & IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE):
        dynamic = True
    if pe.FILE_HEADER.Characterictics & IMAGE_FILE_RELOCS_STRIPPED:
        stripped = True
    if not dynamic or (dynamic and stripped):
        aslr = False
    else:
        aslr = False
    return aslr


class AslrCheck(interfaces.plugins.PluginInterface):
    """Первое, что необходимо сделать при создании подключаемого модуля, — это унаследовать класс PluginInterface .
    Дальше определяются требования; чтобы хорошо сориентироваться в том, какие из них вам нужны, можно просмотреть
    другие подключаемые модули. Каждому модулю нужен слой памяти, и мы указываем это требование первым . Помимо этого
    нам также нужны таблицы символов . Эти два требования можно встретить почти у всех подключаемых модулей.
    В качестве еще одного требования нам понадобится подключаемый модуль pslist, который позволит получить все процессы,
     находящиеся в памяти, и воссоздать из них PE-файлы . Затем мы возьмем каждый из этих файлов и проанализируем его
      на предмет защиты ASLR."""
    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(
                name = 'primary', description='Memory layer for the kernel',
                architectures=["Intel23", "Intel64"]),

                requirements.SymbolTableRequirement(
                    name="nt_symbols", description="Windows kernel symbols"),
            requirements.PluginRequirement(
                name="pslist", plugin=pslist.PsList, version=(1, 0, 0)),
            requirements.ListRequirement(name='pid',
                                         elemnt=int,
                                         description="Process ID to include (all others are excluded)",
                                         option=True,
                                         )
        ]

    @classmethod
    def create_pid_filter(cls, pid_list: List[int] = None):
        """Возможно, нам захочется проверить отдельно взятый процесс с заданным ID, поэтому создадим еще один
         дополнительный параметр, в котором сможем передать список идентификаторов, чтобы ограничить проверку
         соответствующими процессами 

         Для обработки дополнительного ID процесса используется метод класса,
        который создает функцию фильтрации, а она возвращает False для всех
        ID, находящихся в списке. То есть функция фильтрации определяет, будет
        ли процесс отфильтрован (отброшен), поэтому мы возвращаем True только
        в случае, если PID нет в списке"""
        Callable[[interfaces.objects.ObjectInterface], bool]:
        filter_func = lambda _: False
        pid_list = pid_list or []
        filter_list = [x for x in pid_list if x is not None]
        if filter_list:
            filter_func = lambda x: x.UniqueProcessId not in filter_list
        return filter_func

    def _generator(self, procs):
        """Мы создаем специальную структуру данных под названием pe_table_name , которая используется при обходе
        каждого процесса, загруженного в память. Затем берем блок операционного окружения процесса (Process Environment
        Block, PEB), представляющий собой особый регион памяти, и сохраняем его в объект . PEB — это структура данных,
        содержащая множество полезных данных о текущем процессе. Мы записываем этот регион памяти в файлоподобный объект
        (pe_data) , создаем объект PE с помощью библиотеки pefile  и передаем его вспомогательному методу check_aslr.
         В завершение возвращаем с помощью ключевого слова yield кортеж с ID и названием процесса, адресом, по которому
         он размещен в памяти, а также логическим результатом проверки на наличие защиты ASLR """
        pr_table_name = intermed.IntermediateSymbolsTable.create(
            self.context,
            self.config_path,
            "windows",
            "pe",
            class_types=extensions.pe.class_types
        )

        procnames = list()
        for proc in procs:
            procname = proc.ImageFileName.cast("string",
                                               max_length=proc.ImageFileName.vol.count, errors='replace'
                                               )
            if procname in procnames:
                continue
            procnames.append(procname)

            proc_id = "Unknown"
            try:
                proc_id = proc.UniqueProcessId
                proc_layer_name = proc.add_process_layer()
            except exceptions.InvalidAddressException as e:
                vollog.error(f"Process {proc_id}: invalid address {e} in layer {e.layer_name}")
                continue

            peb = self.context.object(
                self.config['nt_symbols'] + constants.BANG + "_PEB",
                layer_name = proc_layer_name, offset = proc.Peb
            )
            try:
                dos_header = self.context.object(
                    pe_table_name + constants.BANG + "_IMAGE_DOS_HEADER",
                    offset=peb.ImageBaseAddress, layer_name=proc_layer_name)
            except Exception as e:
                continue
            pe_data = io.BytesIO()
            for offset, data in dos_header.reconstruct():
                pe_data.seek(offset)
                pe_data.write(data)
            pe_data_raw = pe_data.getvalue()
            pe_data.close()

            try:
                pe = pefile.PE(data=pe_data_raw)
            except Exception as e:
                continue

            aslr = check_aslr()

            yield (0, (proc_id,
                       procname,
                       format_hints.Hex(pe.OPTIONAL_HEADER.ImageBase),
                       aslr,
                       ))

    def run(self):
        """Мы получаем список процессов с помощью подключаемого модуля pslist  и возвращаем данные из генератора,
        используя метод представления TreeGrid . Метод TreeGrid применяется во многих подключаемых модулях, позволяя
        выводить ровно по одной строчке с результатами для каждого проанализированного процесса."""
        procs = pslist.PsList.list_processes(self.context,
                                             self.config["primary"],
                                             self.config["nt_symbols"],
                                             filter_func=self.create_pid_filter(self.config.get('pid', None)))
        return renderers.TreeGrid([
            ("PID", int),
            ("FileName", str),
            ("Base", format_hints.Hex),
            ("ASLR", bool),
        ], self._generator(procs))

