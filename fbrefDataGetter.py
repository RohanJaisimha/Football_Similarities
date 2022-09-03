from constants import *
from bs4 import BeautifulSoup
from functools import reduce
from numpy import isnan

import datetime
import logging
import pandas as pd
import requests
import sys
import unidecode

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

mainDf = pd.DataFrame([])


def getTeamUrlsMap(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    table = soup.find_all("table", {"id": "big5_table"})[0]

    teamUrlsMap = {}
    for td in table.find_all("td", {"data-stat": "team"}):
        teamName = unidecode.unidecode(td.text.strip())
        teamName = teamName.replace(" ", "-")
        teamUrl = td.find("a")["href"].split("/")[3]
        teamCountry = td.nextSibling.text.split()[-1]
        teamUrlsMap[teamName] = [teamUrl, teamCountry]

    return teamUrlsMap


def getTeamData(teamId, season, teamName, teamCountry):
    url = TEAM_URL.format(teamId, season, teamName)
    soup = BeautifulSoup(
        unidecode.unidecode(
            requests.get(url).text.replace("<!--", "").replace("-->", "")
        ),
        "html.parser",
    )

    tableIdPrefixes = [
        "stats_shooting_",
        "stats_passing_",
        "stats_gca_",
        "stats_defense_",
        "stats_possession_",
        "stats_misc_",
        "stats_playing_time_",
    ]

    tables = [
        soup.find("table", {"id": lambda _id: _id and _id.startswith(tableId)})
        for tableId in tableIdPrefixes
    ]

    dfs = []
    for table in tables:
        df = pd.read_html(str(table))[0]
        dfs.append(df)

    teamDf = reduce(lambda df1, df2: pd.concat([df1, df2], join="inner", axis=1), dfs)
    teamDf = teamDf.loc[:, ~teamDf.columns.duplicated()]

    teamDf.insert(2, "Team Name", [teamName.replace("-", " ")] * len(teamDf), True)

    teamDf.insert(3, "Team Country", [teamCountry] * len(teamDf), True)

    global mainDf
    mainDf = mainDf.append(teamDf, ignore_index=True, sort=False)


def scrapeData(season):
    logging.info(f"Scraping {season}...")
    teamUrlsMap = getTeamUrlsMap(BIG_5_TABLE_URL.format(season, season))
    for i, teamName in enumerate(teamUrlsMap):
        if i % (len(teamUrlsMap) // 7) == 0:
            logging.info(f"Scraped {i} teams")
        getTeamData(
            teamUrlsMap[teamName][0], season, teamName, teamUrlsMap[teamName][1]
        )

    mainDf.columns = [
        c[0] + "_" + c[1] if "Unnamed:" not in c[0] else c[1] for c in mainDf.columns
    ]
    mainDf.to_csv(FILENAME_TEMPLATE.format(season))


def isNumeric(a):
    try:
        float(a)
        return True
    except:
        return False


def removeGoalkeepers(df):
    df = df[df["Pos"] != "GK"]
    return df


def removeP90Columns(df):
    columnsToDrop = [column for column in df.columns if "90" in column]
    df = df.drop(columnsToDrop, axis=1)
    return df


def removeMatchesColumns(df):
    columnsToDrop = [column for column in df.columns if column.startswith("Matches")]
    df = df.drop(columnsToDrop, axis=1)
    return df


def removeSquadTotalAndOpponentTotal(df):
    df = df[(df["Player"] != "Squad Total") & (df["Player"] != "Opponent Total")]
    return df


def cleanAgeAndNation(df):
    ages = []
    nations = []
    for i in range(len(df)):
        if not isNumeric(df.iloc[i]["Age"]):
            ages.append(int(df.iloc[i]["Age"].split("-")[0]))
        else:
            ages.append(
                int(df.iloc[i]["Age"])
                if df.iloc[i]["Age"] and not isnan(df.iloc[i]["Age"])
                else None
            )
        if not pd.isnull(df.iloc[i]["Nation"]):
            nations.append(df.iloc[i]["Nation"].split()[-1])
        else:
            nations.append(None)

    df["Age"] = ages
    df["Nation"] = nations
    return df


def cleanPositions(df):
    position1 = []
    position2 = []
    position3 = []

    for i in range(len(df)):
        positions = df.iloc[i]["Pos"].split(",")
        if len(positions) == 1:
            position1.append(positions[0])
            position2.append(None)
            position3.append(None)
        elif len(positions) == 2:
            position1.append(positions[0])
            position2.append(positions[1])
            position3.append(None)
        else:
            position1.append(positions[0])
            position2.append(positions[1])
            position3.append(positions[2])

    df["Position 1"] = position1
    df["Position 2"] = position2
    df["Position 3"] = position3

    df = df.drop("Pos", axis=1)

    return df


def removeUnwantedColumns(df):
    df = df.drop(UNWANTED_COLUMNS, axis=1)
    return df


def renameColumns(df):
    df = df.rename(columns=COLUMNS_RENAMING_MAP)
    return df


def sanitizeData(season):
    logging.info(f"Sanitizing {season}...")
    df = pd.read_csv(FILENAME_TEMPLATE.format(season))

    df = removeP90Columns(df)
    df = removeMatchesColumns(df)
    df = removeUnwantedColumns(df)
    df = removeSquadTotalAndOpponentTotal(df)
    df = removeGoalkeepers(df)
    df = cleanAgeAndNation(df)
    df = cleanPositions(df)
    df = renameColumns(df)

    df.to_csv(FILENAME_TEMPLATE.format(season), index=False)


def main(season):
    scrapeData(season)
    sanitizeData(season)


if __name__ == "__main__":
    main(sys.argv[1])
