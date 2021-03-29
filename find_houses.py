import PySimpleGUI as sg
import requests
import re
import os

from typing import List
from bs4 import BeautifulSoup
from pydantic import BaseModel

city_url = 'https://kladr-rf.ru/35/000/001/'


class Street(BaseModel):
    href: str
    name: str
    tag: str


def getHtml(url) -> str:
    return requests.get(url).text


def parseStreets(streetsTags) -> List[Street]:
    streets: List[Street] = []
    for t in streetsTags:
        tag = str(t.text).split(" ")[-1]
        name = str(t.text)[:-len(tag)]

        streets.append(Street(href=t["href"], name=name, tag=tag))

    return streets


def getStreetHouses(street: Street):
    content = getHtml(street.href)
    soup = BeautifulSoup(content, 'lxml')
    table = soup.find_all("table")[-1]

    rows = table.find_all('tr')
    houses = []
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        line = [ele for ele in cols if ele]
        if len(line) > 0:
            for n in str(line[0]).split(","):
                houses.append(n)

    return houses


def parseKladr(url: str):
    content = getHtml(url)
    soup = BeautifulSoup(content, 'lxml')
    title = soup("meta", {"name": "description"})[0]["content"]

    m = re.search('Классификатор адресов России (.+?),', title)

    if not os.path.exists("csv"):
        os.mkdir("csv")

    if m:
        path = "csv/" + m.group(1).strip() + ".csv"
    else:
        exit(-1)

    print(path)
    file = open(path, "w")

    divs = soup("div", {"class": "span4"})
    div = str(divs[-3]) + str(divs[-2]) + str(divs[-1])
    soup = BeautifulSoup(div, 'lxml')

    streetTags = soup.find_all("a", {"style": ""})

    streets = parseStreets(streetTags)
    i = 0
    n = len(streets)
    for s in streets:
        houses = getStreetHouses(s)
        for h in houses:
            file.write(f"{s.tag}; {s.name}; {h}\n")
        checkClose()
        i += 1
        print(f"{i}/{n}")

    file.close()
    exit(1)


def checkClose():
    event, values = window.read(timeout=1)
    if event == sg.WIN_CLOSED:
        exit(0)


if __name__ == '__main__':
    layout = [
        [sg.Text("Ссылочка на город с https://kladr-rf.ru")],
        [sg.InputText(key="URL")],
        [sg.VSeperator()],
        [sg.Text("", key="OUT", size=(40, 1))],
        [sg.VSeperator()],
        [sg.Button("START", key="START_BTN")]
    ]
    window = sg.Window(title="Zuma ishet doma", layout=layout, margins=(200, 100))

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            exit(0)
        elif event == "START_BTN":
            if values["URL"] == "":
                window.Element("OUT").Update(value="Cсылочку введите плес")
                continue
            else:
                window.Element("OUT").Update(value="")
                parseKladr(values["URL"])
