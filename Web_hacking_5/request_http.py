import requests

url = 'https://ponchik99.pythonanywhere.com/'
response = requests.get(url)

# data = {'user': 'rudenkooleksei@gmail.com', 'passwd': 'rudenkooleksei@gmail.com'}
# response = requests.post(url, data=data)
# print(response.text) # response.text = string; response.content = bytestring

from io import BytesIO
from lxml import etree

content = response.content
print(content)
parser = etree.HTMLParser()
content = etree.parse(BytesIO(content), parser=parser)  # to tree
for link in content.findall('//a'): # find all links a
    print(f'{link.get("href")} -> {link.text}')