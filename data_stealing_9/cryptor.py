""" AES для симметричного шифра  — симметричным его делает то, что для шифрования и расшифровки применяется один и тот
 же ключ. Он очень быстрый и способен справляться с большими объемами текста. Именно с помощью этого метода мы станем
 шифровать информацию, которая будет выводиться за пределы системы"""
from Cryptodome.Cipher import AES, PKCS1_OAEP

"""асимметричный шифр RSA, в котором используются открытые/закрытые ключи. Один ключ (обычно открытый) нужен
для шифрования, а другой (обычно закрытый) — для расшифровки. Мы задействуем RSA, чтобы зашифровать единый ключ, 
применяемый для шифрования с помощью AES. Асимметричная криптография хорошо подходит для небольших наборов информации, 
что делает ее идеальным решением для шифрования ключа AES."""
from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from io import BytesIO

import base64
import zlib


def generate():
    """создать открытый и закрытый ключи для асимметричного алгоритма RSA.
     Данная функция записывает закрытый и открытый ключи в файлы с именами key.pri и key.pub"""
    new_key = RSA.generate(2048)
    private_key = new_key.exportKey()
    public_key = new_key.public_key().exportKey()

    with open('key.pri', 'wb') as f:
        f.write(private_key)

    with open('key.pub', 'wb') as f:
        f.write(public_key)


def get_rsa_cipher(keytype):
    """передаем этой функции тип ключа (pub или pri), читаем соответствующий
    файл и возвращаем шифр и размер RSA-ключа в байтах"""
    with open(f'key.{keytype}') as f:
        key = f.read()
    rsakey = RSA.importKey(key)
    return (PKCS1_OAEP.new(rsakey), rsakey.size_in_bytes())


def encrypt(plaintext):
    compressed_text = zlib.compress(plaintext)  #  передаем обычный текст в виде байтов и сжимаем его
    session_key = get_random_bytes(16)     # случайным образом генерируем ключ сеанса
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(compressed_text)  # шифруем  сжатый текст с помощью шифра AES

    cipher_rsa, _ = get_rsa_cipher('pub')

    # нужно вернуть ключ сеанса вместе с зашифрованным текстом, чтобы его можно было расшифровать на другой стороне.
    # Для шифруем ключ сеанса с использованием RSA-ключа, сгенерированного из содержимого файла key.pub
    encrypt_session_key = cipher_rsa.encrypt(session_key)

    # Вся информация, которую нужно будет расшифровать, помещается в переменную msg_payload
    msg_payload = encrypt_session_key + cipher_aes.nonce + tag + ciphertext
    ecrypted = base64.encodebytes(msg_payload)  # кодируемую в формате base64 и возвращаемую в виде итоговой зашифрованной строки
    return ecrypted

def decrypt(encrypted):
    """Для расшифровки мы выполняем шаги из функции encrypt в обратном порядке"""
    encrypted_bytes = BytesIO(base64.decodebytes(encrypted))  # преобразуем строку, закодированную как base64, в байты
    cipher_rsa, keysize_in_bytes = get_rsa_cipher('pri')

    # считываем из расшифрованной байтовой строки  зашифрованный
    # ключ сеанса вместе с другими параметрами, которые нужно расшифровать
    encrypted_session_key = encrypted_bytes.read(keysize_in_bytes)
    nonce = encrypted_bytes.read(16)
    tag = encrypted_bytes.read(16)
    ciphertext = encrypted_bytes.read()

    session_key = cipher_rsa.decrypt(encrypted_session_key)  # Расшифровываем ключ сеанса с помощью закрытого RSA-ключа

    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    decrypted = cipher_aes.decrypt_and_verify(ciphertext, tag)  # используем полученный результат в сочетании с шифром AES для расшифровки самого сообщения

    plaintext = zlib.decompress(decrypted)  # распаковываем полученное в байтовую строку, представляющую собой обычный текст
    return plaintext


if __name__ == '__main__':
    # generate()  # Открытый и закрытый ключи генерируются вместе . Мы просто вызываем функцию generate, поскольку, чтобы пользоваться ключами, их сначала нужно создать
    plaintext = b'hey there you'
    print(decrypt(encrypt(plaintext)))