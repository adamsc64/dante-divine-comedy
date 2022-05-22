#!/usr/bin/env python3
"""
Generates HTML that links to audio of Dante's Divine Comedy and
commentary. Prints to stdout.
"""
from string import Template

from bs4 import BeautifulSoup
import requests


DIVINE_COMEDY = "https://librivox.org/the-divine-comedy-version-2-dramatic-reading-by-dante-alighieri/"
PODCAST = "https://feeds.soundcloud.com/users/soundcloud:users:989590753/sounds.rss"
CANTICLE_ORDER = ["inferno", "purgatorio", "paradiso"]
RENAMES = {
    "purgatory": "purgatorio",
    "puragtorio": "purgatorio",
}


class Canto:
    def __init__(self, canticle, number):
        self.canticle = canticle
        self.number = number
        self.mp3_url = None
        self.podcast_url = None

    def validate(self):
        if not self.mp3_url:
            raise ValueError(f"{self}.mp3_url={self.mp3_url}")
        if not self.podcast_url:
            raise ValueError(f"{self}.podcast_url={self.podcast_url}")
        if not self.canticle:
            raise ValueError(f"{self}.canticle={self.canticle}")
        if not self.number:
            raise ValueError(f"{self}.number={self.number}")

    def __repr__(self):
        return f'Canto("{self.canticle}", {self.number})'


def main():
    inferno = [Canto("inferno", number) for number in range(1, 34 + 1)]
    purgatorio = [Canto("purgatorio", number) for number in range(1, 33 + 1)]
    paradiso = [Canto("paradiso", number) for number in range(1, 33 + 1)]
    CANTICLES = {
        "inferno": inferno,
        "purgatorio": purgatorio,
        "paradiso": paradiso,
    }
    readings = get_readings()
    podcast = get_podcast()

    for canticle_name, number, mp3_url in readings:
        if canticle_name == "inferno":
            canticle = inferno
        elif canticle_name == "purgatorio":
            canticle = purgatorio
        elif canticle_name == "paradiso":
            canticle = paradiso
        else:
            raise ValueError(f"invalid canticle {canticle_name}")
        canticle[number - 1].mp3_url = mp3_url
    for canticle_name, number, podcast_url in podcast:
        if canticle_name == "inferno":
            canticle = inferno
        elif canticle_name == "purgatorio":
            canticle = purgatorio
        elif canticle_name == "paradiso":
            canticle = paradiso
        else:
            raise ValueError(f"invalid canticle {canticle_name}")
        canticle[number - 1].podcast_url = podcast_url

    for canto in inferno:
        canto.validate()
    for canto in purgatorio:
        canto.validate()
    for canto in paradiso:
        canto.validate()
    T_th = Template("<th>$content</th>")
    T_td = Template("<td>$content</td>")
    T_a = Template(
        '<audio controls preload="none"> <source src="$link" type="audio/mpeg"> No support</audio>'
    )
    T_tr = Template("<tr>$td1 $td2 $td3</tr>")
    T_thead = Template("<thead>$content</thead>")
    T_tbody = Template("<tbody>$content</tbody>")
    T_table = Template("<table>$thead<tbody>$tbody</tbody></table>")
    T_html = Template("<html><head></head><body>$content</body></html>")
    T_div = Template("<div>$content</div>")
    th_titles = ["Canto", "Text", "Commentary"]
    th_elements = "".join([T_th.substitute(content=th_title) for th_title in th_titles])
    div = "<h1>The Divine Comedy by Dante Alighieri</h1>"
    for canticle_name in CANTICLE_ORDER:
        canticle = CANTICLES[canticle_name]
        div += f"<h2>{canticle_name.capitalize()}</h2>"
        thead = T_thead.substitute(content=th_elements)
        tbody = ""
        for canto in canticle:
            tbody += T_tr.substitute(
                td1=T_td.substitute(
                    content=f"{canto.canticle.capitalize()} {canto.number}"
                ),
                td2=T_td.substitute(
                    content=T_a.substitute(text="Reading", link=canto.mp3_url)
                ),
                td3=T_td.substitute(
                    content=T_a.substitute(text="Commentary", link=canto.podcast_url)
                ),
            )
        tbody = T_tbody.substitute(content=tbody)
        table = T_table.substitute(thead=thead, tbody=tbody)
        div += table
    div += '<p>Sources: LibriVox "Divine Comedy (version 2 Dramatic Reading)", Baylor University 100 Days of Dante.</p>'
    div += '<p>Created by <a href="https://www.instagram.com/adamsc64/">Christopher Adams</a></p>'
    div = T_div.substitute(content=div)
    html_output = T_html.substitute(content=div)
    print(BeautifulSoup(html_output, features="html5lib").prettify())


def get_readings():
    content = requests.get(DIVINE_COMEDY).content
    soup = BeautifulSoup(content, features="html5lib")
    chapters = soup.find_all("a", "chapter-name")
    for chapter in chapters:
        if "Dramatis Personae" in chapter.text:
            continue
        mp3_url = chapter.attrs["href"]
        _, _, canticle, number = chapter.text.split()
        canticle = canticle.lower()
        if canticle in RENAMES:
            canticle = RENAMES[canticle]
        number = from_numeral(number)
        yield (canticle, number, mp3_url)


def get_podcast():
    content = requests.get(PODCAST).content
    soup = BeautifulSoup(content, features="html5lib")
    episodes = soup.find_all("item")
    for episode in episodes:
        title = episode.find("title")
        title = title.decode_contents()
        podcast_url = episode.find("enclosure")
        podcast_url = podcast_url.attrs["url"]
        canticle, number, number_maybe = title.split()[0:3]
        canticle = canticle.lower()
        if canticle in RENAMES:
            canticle = RENAMES[canticle]
        try:
            number = int(number)
        except ValueError:
            number = int(number_maybe)
        yield (canticle, number, podcast_url)


def from_numeral(roman):
    roman = roman.upper()
    conv = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
        "IV": 4,
        "IX": 9,
        "XL": 40,
        "XC": 90,
        "CD": 400,
        "CM": 900,
    }
    i = 0
    num = 0
    while i < len(roman):
        if i + 1 < len(roman) and roman[i : i + 2] in conv:
            num += conv[roman[i : i + 2]]
            i += 2
        else:
            num += conv[roman[i]]
            i += 1
    return num


if __name__ == "__main__":
    main()
