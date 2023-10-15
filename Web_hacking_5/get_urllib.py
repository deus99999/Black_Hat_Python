import urllib.parse
import urllib.request

url = 'https://ponchik99.pythonanywhere.com/'
with urllib.request.urlopen(url) as response:  # GET
    content = response.read()
print(content)




