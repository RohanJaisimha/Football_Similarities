from apscheduler.triggers.interval import IntervalTrigger
from constants import *
from flask_apscheduler import APScheduler
from flask import Flask
from flask import session
from flask import render_template
from flask import request
from flask_session import Session
from functools import reduce
from itertools import chain
from sklearn.preprocessing import MinMaxScaler

import fbrefDataGetter
import heapq
import json
import os
import pandas as pd
import re


application = Flask(__name__)

SECRET_KEY = os.urandom(24)
SESSION_TYPE = "filesystem"
application.config.from_object(__name__)
Session(application)

scheduler = APScheduler()
scheduler.init_app(application)
scheduler.start()
for season in SEASONS:
    application.apscheduler.add_job(
        func=fbrefDataGetter.main,
        args=[season],
        trigger=IntervalTrigger(hours=24, jitter=15 * 60),
        id=f"dataScraper_{season}",
    )


@application.route("/")
def home():
    dataFiles = os.listdir("./Data")
    seasons = map(lambda s: re.search("\d+-\d+", s).group(), dataFiles)
    return render_template(
        "home.html",
        seasons=seasons,
    )


def prepareDf():
    season = session["season"]

    filename = "./Data/Top5Leagues_{}.csv".format(season)
    df = pd.read_csv(filename)
    session["df"] = df.to_json()
    convertDfToPer90()
    scaleDf()


def convertDfToPer90():
    df = pd.read_json(session["df"])

    columnsToBePer90 = reduce(chain, ATTRIBUTES.values())
    for column in columnsToBePer90:
        df[column] = df[column] / df["Minutes"] * 90

    session["df"] = df.to_json()


def scaleDf():
    df = pd.read_json(session["df"])

    attributesToBeScaled = list(set(df.columns) - set(ATTRIBUTES_NOT_TO_BE_SCALED))

    scaler = MinMaxScaler()
    df[attributesToBeScaled] = scaler.fit_transform(df[attributesToBeScaled])

    session["df"] = df.to_json()


def getTeams():
    df = pd.read_json(session["df"])

    teams = {}
    for i in range(len(df)):
        player = df.iloc[i]
        teamCountry = player["Team Country"]
        teamName = player["Team Name"]
        if teamCountry not in teams:
            teams[teamCountry] = set()
        teams[teamCountry].add(teamName)

    for teamCountry in teams:
        teams[teamCountry] = sorted(list(teams[teamCountry]))

    return teams


@application.route("/similarities/<season>", methods=["GET"])
def similarities(season):
    session["season"] = season
    prepareDf()
    df = pd.read_json(session["df"])

    ageRange = range(int(min(df["Age"])), int(max(df["Age"])) + 1)
    teams = getTeams()
    playerNames = list(df["Player Name"])

    return render_template(
        "similarities.html",
        ATTRIBUTES=ATTRIBUTES,
        positions=POSITIONS,
        ageRange=ageRange,
        teams=teams,
        playerNames=playerNames,
    )


@application.route("/findSimilarities", methods=["POST"])
def findSimilarities():
    playerName = request.form["playerName"]
    attributesToConsider = json.loads(request.form["attributesToConsider"])
    teamsToConsider = json.loads(request.form["teamsToConsider"])
    positionsToConsider = json.loads(request.form["positionsToConsider"])
    minAge = int(request.form["minAge"])
    maxAge = int(request.form["maxAge"])
    k = int(request.form["k"])

    removeUnneededRowsAndColumns(
        playerName,
        teamsToConsider,
        attributesToConsider,
        positionsToConsider,
        minAge,
        maxAge,
    )
    similarityScores = getSimilarityScores(playerName, attributesToConsider)
    kMostSimilarPlayers = getKMostSimilarPlayers(similarityScores, k)

    prepareDf()

    return json.dumps(kMostSimilarPlayers)


def removeUnneededRowsAndColumns(
    playerName,
    teamsToConsider,
    attributesToConsider,
    positionsToConsider,
    minAge,
    maxAge,
):
    df = pd.read_json(session["df"])

    df = df[
        attributesToConsider
        + [
            "Player Name",
            "Nationality",
            "Team Name",
            "Position 1",
            "Position 2",
            "Position 3",
            "Age",
        ]
    ]
    df = df[(df["Player Name"] == playerName) | (df["Team Name"].isin(teamsToConsider))]
    df = df[
        (df["Player Name"] == playerName)
        | (df["Position 1"].isin(positionsToConsider))
        | (df["Position 2"].isin(positionsToConsider))
        | (df["Position 3"].isin(positionsToConsider))
    ]
    df = df[
        (df["Player Name"] == playerName)
        | ((df["Age"] >= minAge) & (df["Age"] <= maxAge))
    ]

    session["df"] = df.to_json()


def getSimilarityScores(playerName, attributesToConsider):
    df = pd.read_json(session["df"])

    similarityScores = []
    mainPlayer = df[df["Player Name"] == playerName].iloc[0]

    for i in range(len(df)):
        otherPlayer = df.iloc[i]
        similarityScore = 0
        for attributeToConsider in attributesToConsider:
            similarityScore += (
                mainPlayer[attributeToConsider] - otherPlayer[attributeToConsider]
            ) ** 2
        similarityScore **= 0.5

        position = "{}{}{}{}{}".format(
            otherPlayer["Position 1"],
            POSITIONS_DELIMITER,
            otherPlayer["Position 2"],
            POSITIONS_DELIMITER,
            otherPlayer["Position 3"],
        )
        position = position.replace(POSITIONS_DELIMITER + "nan", "")
        position = position.replace(POSITIONS_DELIMITER + "None", "")

        similarityScores.append(
            [
                similarityScore,
                otherPlayer["Player Name"],
                otherPlayer["Nationality"],
                otherPlayer["Team Name"],
                position,
                int(otherPlayer["Age"]),
            ]
        )

    return similarityScores


def getKMostSimilarPlayers(similarityScores, k):
    heapq.heapify(similarityScores)

    kMostSimilarPlayers = []

    for i in range(min(k, len(similarityScores))):
        similarPlayer = heapq.heappop(similarityScores)
        kMostSimilarPlayers.append(similarPlayer[1:])

    return kMostSimilarPlayers


if __name__ == "__main__":
    application.run(debug=True, port=5000, host="0.0.0.0")
