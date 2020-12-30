from bs4 import BeautifulSoup
import requests
import unidecode
import pandas as pd
from functools import reduce
from fbref_constants import *
import re


overall_df = pd.DataFrame([])


def get_team_urls_map(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    table = soup.find_all("table", {"id": "big5_table"})[0]

    team_urls_map = {}
    for td in table.find_all("td", {"data-stat": "squad"}):
        team_name = unidecode.unidecode(td.text.strip())
        team_name = team_name.replace(" ", "-")
        team_url = td.find("a")["href"].split("/")[3]
        team_country = td.nextSibling.text.split()[-1]
        team_urls_map[team_name] = [team_url, team_country]

    return team_urls_map


def get_team_data(team_id, season, team_name, team_country):
    url = TEAM_URL.format(team_id, season, team_name)
    soup = BeautifulSoup(
        unidecode.unidecode(
            requests.get(url).text.replace("<!--", "").replace("-->", "")
        ),
        "html.parser",
    )

    players = {}

    table_id_prefixes = [
        "stats_shooting_",
        "stats_passing_",
        "stats_gca_",
        "stats_defense_",
        "stats_possession_",
        "stats_misc_",
        "stats_playing_time_",
    ]

    tables = [
        soup.find("table", {"id": lambda _id: _id and _id.startswith(table_id)})
        for table_id in table_id_prefixes
    ]

    dfs = []
    for table in tables:
        df = pd.read_html(str(table))[0]
        dfs.append(df)

    team_df = reduce(lambda df1, df2: pd.concat([df1, df2], join="inner", axis=1), dfs)
    team_df = team_df.loc[:, ~team_df.columns.duplicated()]

    team_df.insert(2, "Team Name", [team_name.replace("-", " ")] * len(team_df), True)

    team_df.insert(3, "Team Country", [team_country] * len(team_df), True)

    global overall_df
    overall_df = overall_df.append(team_df, ignore_index=True, sort=False)


def main():
    team_urls_map = get_team_urls_map(BIG_5_TABLE_URL.format(SEASON, SEASON))
    for i, team_name in enumerate(team_urls_map):
        if i % (len(team_urls_map) // 10) == 0:
            print(i)
        get_team_data(
            team_urls_map[team_name][0], SEASON, team_name, team_urls_map[team_name][1]
        )

    overall_df.columns = [
        c[0] + "_" + c[1] if "Unnamed:" not in c[0] else c[1]
        for c in overall_df.columns
    ]
    overall_df.to_csv(FILENAME)


if __name__ == "__main__":
    main()
