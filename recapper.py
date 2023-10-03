from scapy.all import TCP, rdpcap
import collections
import os
import re
import sys
import zlib

OUTDIR = '/root/Desktop/pictures'
PCAPS = '/root/Downloads'

Response = collections.namedtuple('Response', ['header', 'payload'])


def get_header(payload):
    """Функция get_header принимает необработанный HTTP-трафик и выдает заголовки. Чтобы извлечь заголовок, переходим
    в самое начало содержимого и ищем две пары символов — возврата каретки и перевода строки. Если ничего не удается
    найти, мы получим исключение ValueError, в этом случае просто выведем в консоль дефис (-) и завершим работу. Если
    поиск окажется успешным, мы создадим словарь (header), разбив декодированное содержимое на части, так чтобы ключ
    находился перед двоеточием, а значение — после него. Если заголовок не содержит ключа Content-Type, возвращаем None,
     сигнализируя об отсутствии данных, которые нужно извлечь"""
    try:
        header_raw = payload[:payload.index(b'\r\n\r\n') + 2]
    except ValueError:
        sys.stdout.write('-')
        sys.stdout.flush()
        return None

    header = dict(re.findall((r'(?P<name>.*?): (?<value>.*?)\r\n',
                              header_raw.decode())))
    if 'Content-Type' not in header:
        return None
    return header


def extract_content(Response, content_name='image'):
    """ принимает HTTP-ответ и тип содержимого, которое мы хотим извлечь. Response — это namedtuple с двумя
        атрибутами, header и payload. Если содержимое было закодировано с помощью инструмента gzip или deflate, мы его
        распаковываем, используя модуль zlib. Если ответ содержит изображение, в атрибуте Content-Type его заголовка
        будет находиться подстрока image (например, image/png или image/jpg). В таком случае мы создаем переменную с
        именем content_type и присваиваем ей тип содержимого, указанный в заголовке. Для хранения самого содержимого
        (всего, что идет после заголовка) используем еще одну переменную. В конце возвращаем кортеж с content и content_type"""

    content, content_type = None, None
    if content_name in Response.header['Content-Type']:
        content_type = Response.header['Content-Type'].split('/')[1]
        content = Response.payload[Response.payload.index(b'\r\n\r\n') + 4]

        if 'Content-Encoding' in Response.header:
            if Response.header['Content-Encoding'] == "gzip":
                content = zlib.decompress(Response.payload, zlib.MAX_WBITS | 32)
            elif Response.header['Content-Encoding'] == "deflate":
                content = zlib.decompress(Response.payload)

    return content, content_type


class Recapper:
    def __init__(self, fname):
        pcap = rdpcap(fname)
        self.sessions = pcap.sessions()  #  разибиие TCP-потока на отдельные сеансы и сохранение их в виде словаря
        self.responses = list()         #  список для ответов из рсар файла

    def get_responses(self):
        """пройдемся по потоку пакетов в поиске каждого отдельного ответа и добавим найденное в список responses"""
        for session in self.sessions:
            payload = b''
            for packet in self.sessions[session]:
                try:
                    if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                        payload += bytes(packet[TCP].payload)
                except IndexError:
                    sys.stdout.write('x')
                    sys.stdout.flush()

            if payload:
                header = get_header(payload)  # get_header позволяет анализировать HTTP-заголовки по отдельности
                if header is None:
                    continue
                self.responses.append(Response(header=header, payload=payload))

    def write(self, content_name):
        """перебираем список ответов в поиске изображения и, если оно найдено, записываем его на диск с помощью метода write"""
        for i, response in enumerate(self.responses):
            content, content_type = extract_content(response, content_name)
            if content and content_type:
                fname = os.path.join(OUTDIR, f'ex_{i}.{content_type}')
                print(f'Writing {fname}')
                with open(fname, 'wb') as f:
                    f.write(content)


if __name__ == '__main__':
    pfile = os.path.join(PCAPS, 'pcap.pcap')
    recapper = Recapper(pfile)
    recapper.get_responses()
    recapper.write('image')
