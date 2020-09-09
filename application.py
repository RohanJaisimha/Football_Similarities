import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import unidecode
import heapq
from flask import Flask, render_template, request
import json
from attributes_and_teams import *

# import difflib
from fuzzywuzzy.fuzz import partial_ratio

application = Flask(__name__)

players_df = None


def loadData(f_name):
    global players_df

    players_df = pd.read_csv(f_name)
    players_df = players_df.drop(
        [
            "birth_year",
            "games",
            "games_starts",
            "position",
            "nationality",
            "minutes_90s",
            "goals_per90",
            "assists_per90",
            "goals_assists_per90",
            "goals_pens_per90",
            "goals_assists_pens_per90",
            "xg_per90",
            "xa_per90",
            "xg_xa_per90",
            "npxg_per90",
            "npxg_xa_per90",
            "shots_total_per90",
            "shots_on_target_per90",
            "sca_per90",
            "gca_per90",
        ],
        axis=1,
    )

    players_df["player"] = pd.Series(
        [unidecode.unidecode(name) for name in players_df["player"]]
    )
    players_df = players_df.rename(columns={"player": "name"})

    players_df = players_df[players_df["minutes"] >= 500]
    players_df.index = range(len(players_df))

    # converting stats to per 90
    columns_not_to_be_per90 = ["name", "minutes", "age", "squad"] + [
        col for col in players_df.columns if "_pct" in col
    ]

    for col in players_df.columns:
        if col not in columns_not_to_be_per90:
            players_df[col + "_per90"] = players_df[col] / players_df["minutes"] * 90
            players_df = players_df.drop([col], axis=1)

    players_df = players_df.drop(["minutes"], axis=1)


def scaleData():
    global players_df

    columns_not_to_be_scaled = ["name", "squad"]
    columns_to_be_scaled = [
        col for col in players_df.columns if col not in columns_not_to_be_scaled
    ]
    scaler = MinMaxScaler()
    players_df[columns_to_be_scaled] = scaler.fit_transform(
        players_df[columns_to_be_scaled]
    )


def getDistance(p1, p2, attributes_to_compare):
    d = 0
    num_attributes = 0
    for attribute in attributes_to_compare:
        if attribute in ["name", "squad"]:
            continue
        num_attributes += 1
        if type(p1[attribute]) is not str:
            # euclidean distance
            d = d + (p1[attribute] - p2[attribute]) ** 2
        else:
            # hamming distance: 1 if unequal, 0 if equal
            d = d + int(p1[attribute] != p2[attribute])
    return d ** 0.5


def findkNN(player, k=5, attributes_to_compare=[]):
    global players_df

    distances = []
    for i in range(len(players_df)):
        other_player = players_df.iloc[i]
        distance = getDistance(player, other_player, attributes_to_compare)
        name = other_player["name"]
        squad = other_player["squad"]
        distances.append([distance, name, squad])

    heapq.heapify(distances)

    similar_players = []

    i = 0
    while i < k and i < len(players_df):
        distance, player_name, squad = heapq.heappop(distances)
        score = round((1 - distance / len(attributes_to_compare)) * 100, 3)
        score = str("{:.3f}".format(score))
        similar_players.append([player_name, squad, score])
        i += 1

    return similar_players


def filterData(min_age, max_age, player_name, team_name, teams, attributes_to_compare):
    global players_df

    for i in range(len(players_df)):
        player = players_df.iloc[i]
        if min_age <= player["age"] <= max_age and player["squad"] in teams:
            pass
        elif player["name"] == player_name and player["squad"] == team_name:
            pass
        else:
            players_df["name"].iloc[i] = "undefined"

    players_df = players_df[players_df["name"] != "undefined"]
    players_df = players_df[attributes_to_compare + ["name", "squad"]]


@application.route("/")
def index():
    global players_df

    overall_max_age = max(players_df["age"])
    overall_min_age = min(players_df["age"])

    return render_template(
        "index.html",
        overall_min_age=overall_min_age,
        overall_max_age=overall_max_age,
        attacking_attributes=attacking_attributes,
        defensive_attributes=defensive_attributes,
        dribbling_attributes=dribbling_attributes,
        passing_attributes=passing_attributes,
        discipline_attributes=discipline_attributes,
        english_teams=english_teams,
        spanish_teams=spanish_teams,
        german_teams=german_teams,
        italian_teams=italian_teams,
        french_teams=french_teams,
    )


@application.route("/findSimilarities", methods=["POST"])
def findSimilarities():
    global players_df

    min_age, max_age = json.loads(request.form["age_range"])
    k = int(request.form["k"])
    player_name = request.form["player_name"]
    team_name = request.form["team_name"]
    attributes_to_compare = json.loads(request.form["attributes"])
    teams = json.loads(request.form["teams"])

    if not teams:
        # if no teams are passed, use all of them
        teams = (
            english_teams + spanish_teams + german_teams + italian_teams + french_teams
        )

    if not attributes_to_compare:
        # if no attrbiutes are passed, use all of them
        attributes_to_compare = (
            attacking_attributes
            + defensive_attributes
            + dribbling_attributes
            + passing_attributes
            + discipline_attributes
        )

    filterData(min_age, max_age, player_name, team_name, teams, attributes_to_compare)
    scaleData()

    try:
        player = players_df[
            (players_df["name"] == player_name) & (players_df["squad"] == team_name)
        ].iloc[0]
    except IndexError:
        return json.dumps(["ERROR"])
    players_df = players_df[
        (players_df["name"] != player_name) | (players_df["squad"] != team_name)
    ]

    similar_players = findkNN(player, k, attributes_to_compare)
    loadData("./Data/Top5Leagues_201920_Stats.csv")
    return json.dumps(similar_players)


@application.route("/searchPlayers", methods=["POST"])
def searchPlayers():
    query = request.form["query"]

    closest_matches = []
    word_closeness_scores = [
        [-partial_ratio(query.lower(), word.lower()), word]
        for word in list(players_df["name"] + ", " + players_df["squad"])
    ]
    heapq.heapify(word_closeness_scores)

    for i in range(3):
        closest_matches.append(heapq.heappop(word_closeness_scores)[1])

    return json.dumps(closest_matches)


loadData("./Data/Top5Leagues_201920_Stats.csv")

if __name__ == "__main__":
    application.run(debug=True, port="5000", host="0.0.0.0")
