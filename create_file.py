from datetime import datetime
import os

text = input("Type Anything and click enter: ")

today = datetime.today().strftime('%d-%M-%Y')
timestamp = datetime.now().timestamp()
try:
    os.mkdir('randomtext')
except:
    ...

with open(f'randomtext/{today}_{timestamp}.txt', "w+") as file:
    file.write(text)
print("Check the randomtext folder")