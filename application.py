import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import heapq
from flask import Flask, render_template, request
import json
import os
import re
from constants import *
import random

application = Flask(__name__)

df = None
SEASON = None


@application.route("/")
def home():
    data_files = os.listdir("./Data")
    seasons = map(lambda s: re.search("\d+-\d+", s).group(), data_files)
    return render_template(
        "home.html",
        seasons=seasons,
    )


def prepareDf():
    global df

    filename = "./Data/Top5Leagues_{}.csv".format(SEASON)
    df = pd.read_csv(filename)
    scaleDf()


@application.route("/similarities/<season>", methods=["GET"])
def similarities(season):
    global SEASON
    global df

    SEASON = season
    prepareDf()

    positions = ["DF", "MF", "FW"]
    age_range = range(int(min(df["Age"])), int(max(df["Age"])) + 1)
    teams = getTeams()
    player_names = list(df["Player Name"])

    return render_template(
        "similarities.html",
        ATTRIBUTES=ATTRIBUTES,
        positions=positions,
        age_range=age_range,
        teams=teams,
        player_names=player_names
    )


@application.route("/findSimilarities", methods=["POST"])
def findSimilarities():
    player_name = request.form["player_name"]
    attributes_to_consider = json.loads(request.form["attributes_to_consider"])
    teams_to_consider = json.loads(request.form["teams_to_consider"])
    positions_to_consider = json.loads(request.form["positions_to_consider"])
    min_age = int(request.form["min_age"])
    max_age = int(request.form["max_age"])
    k = int(request.form["k"])

    removeUnneededRowsAndColumns(
        player_name,
        teams_to_consider,
        attributes_to_consider,
        positions_to_consider,
        min_age,
        max_age,
    )
    similarity_scores = getSimilarityScores(player_name, attributes_to_consider)
    k_most_similar_players = getKMostSimilarPlayers(similarity_scores, k)

    prepareDf()

    return json.dumps(k_most_similar_players)

def removeUnneededRowsAndColumns(
    player_name,
    teams_to_consider,
    attributes_to_consider,
    positions_to_consider,
    min_age,
    max_age,
):
    global df

    df = df[
        attributes_to_consider
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
    df = df[
        (df["Player Name"] == player_name) | (df["Team Name"].isin(teams_to_consider))
    ]
    df = df[
        (df["Player Name"] == player_name)
        | (df["Position 1"].isin(positions_to_consider))
        | (df["Position 2"].isin(positions_to_consider))
        | (df["Position 3"].isin(positions_to_consider))
    ]
    df = df[
        (df["Player Name"] == player_name)
        | ((df["Age"] >= min_age) & (df["Age"] <= max_age))
    ]


def getSimilarityScores(player_name, attributes_to_consider):
    global df

    similarity_scores = []
    main_player = df[df["Player Name"] == player_name].iloc[0]
    # df = df.drop(main_player)

    for i in range(len(df)):
        other_player = df.iloc[i]
        similarity_score = 0
        for attribute_to_consider in attributes_to_consider:
            similarity_score += (
                main_player[attribute_to_consider] - other_player[attribute_to_consider]
            ) ** 2
        similarity_score **= 0.5
        position = "{},{},{}".format(
            other_player["Position 1"],
            other_player["Position 2"],
            other_player["Position 3"],
        )
        position = position.replace(",nan", "")
        similarity_scores.append(
            [
                similarity_score,
                other_player["Player Name"],
                other_player["Nationality"],
                other_player["Team Name"],
                position,
                other_player["Age"],
            ]
        )

    return similarity_scores


def getKMostSimilarPlayers(similarity_scores, k):
    heapq.heapify(similarity_scores)

    k_most_similar_players = []

    for i in range(min(k, len(similarity_scores))):
        similar_player = heapq.heappop(similarity_scores)
        k_most_similar_players.append(similar_player[1:])

    return k_most_similar_players


def scaleDf():
    global df
    attributes_not_to_be_scaled = [
        "Player Name",
        "Nationality",
        "Team Name",
        "Position 1",
        "Position 2",
        "Position 3",
        "Age",
        "Team Country",
    ]
    attributes_to_be_scaled = list(set(df.columns) - set(attributes_not_to_be_scaled))

    scaler = MinMaxScaler()
    df[attributes_to_be_scaled] = scaler.fit_transform(df[attributes_to_be_scaled])


def getTeams():
    global df

    teams = {}
    for i in range(len(df)):
        player = df.iloc[i]
        team_country = player["Team Country"]
        team_name = player["Team Name"]
        if team_country not in teams:
            teams[team_country] = set()
        teams[team_country].add(team_name)

    for team_country in teams:
        teams[team_country] = sorted(list(teams[team_country]))

    return teams


if __name__ == "__main__":
    application.run(debug=True, port=5000, host="0.0.0.0")
