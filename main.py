from functools import cache
from timeit import timeit
from typing import Union
from requests import get
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from multiprocessing.pool import ThreadPool
from matplotlib import pyplot as plt

SUBJECT_CODE = {
    "Mathematical Methods": 32,
    "Specialist Mathematics": 42,
    "English": 16,
    "Physics": 39,
    "Digital Solutions": 11,
}

SUBJECT_ABBRV = {
    "MAM": "Mathematical Methods",
    "MAS": "Specialist Mathematics",
    "ENG": "English",
    "PHY": "Physics",
    "DIS": "Digital Solutions",
}


def name_to_code(name: str) -> int:
    if name.title() in SUBJECT_CODE.keys():
        return SUBJECT_CODE[name]
    elif name.upper() in SUBJECT_ABBRV.keys():
        return SUBJECT_CODE[SUBJECT_ABBRV[name]]
    return 0


def construct_args(results: dict[str, float]):
    args: dict[str, float] = {}
    for key, value in results.items():
        args[f"score[{name_to_code(key)}]"] = value
    return str(args).replace(" ", "").replace("'", '"')


SERVICE = Service(ChromeDriverManager().install())


@cache
def get_service():
    return Service(ChromeDriverManager().install())


def get_atar_soup(raw_results: dict[str, float]):
    url = "https://qce.atarcalc.com/#" + construct_args(raw_results)
    # html = get(url).text
    # soup = bs4.BeautifulSoup(html, "html.parser")

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    service = get_service()

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    return soup


def get_atar(raw_results: dict[str, float]):
    response = {"atar": 0.0, "raw_results": {}, "scaled_results": {}}
    soup = get_atar_soup(raw_results)
    estimate_tag = soup.find("span", {"class": "estimated_atar"})
    if estimate_tag:
        try:
            response["atar"] = float(estimate_tag.text)
        except ValueError:
            response["atar"] = 0.0

    scaling_table = soup.find("table", {"class": "subject_results_one"})
    if scaling_table:
        scaling_table_body = scaling_table.find("tbody")
        for row in scaling_table_body.find_all("tr"):  # type: ignore
            cells = row.find_all("td")
            response["raw_results"][cells[0].text] = float(cells[1].text)
            response["scaled_results"][cells[0].text] = float(cells[2].text)

    return response


def main(results: dict[str, float]):
    atar = get_atar(results)
    print(atar)


def thr(args):
    subjects, score = args
    return get_atar({k: score for k in subjects})


def fit_scaling():
    subjects = SUBJECT_CODE.keys()
    points = {subject: [] for subject in subjects}
    threadres = ThreadPool().map(thr, [(subjects, score) for score in range(0, 100, 5)])
    for res in threadres:
        for k in res["raw_results"]:
            points[k].append((res["raw_results"][k], res["scaled_results"][k]))

    for k in points:
        plt.scatter(*zip(*points[k]))  # type: ignore
    plt.show()


if __name__ == "__main__":
    results = {
        "MAM": 79.7,
        "Digital Solutions": 91.5,
        "MAS": 65.0,
        "ENG": 75.5,
        "PHY": 79.05,
    }
    main(results)
