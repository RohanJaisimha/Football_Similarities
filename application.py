import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import unidecode
import heapq
from flask import Flask, render_template, request
import json

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

    # scaling
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


def findkNN(player, k=5, attributes_to_compare=None):
    global players_df
    if not attributes_to_compare:
        # if no attrbiutes are passed, use all of them
        attributes_to_compare = player.index

    distances = []
    for i in range(len(players_df)):
        distance = getDistance(player, players_df.iloc[i], attributes_to_compare)
        name = players_df.iloc[i]["name"]
        squad = players_df.iloc[i]["squad"]
        distances.append([distance, name, squad])

    heapq.heapify(distances)

    similar_players = []

    for i in range(k + 1):
        distance, player_name, squad = heapq.heappop(distances)
        if i == 0:
            # the lowest distance to a player is always that player themselves,
            # so we can ignore that the first match
            continue
        score = round((1 - distance / len(attributes_to_compare)) * 100, 3)
        similar_players.append([player_name, squad, score])

    return similar_players


@application.route("/")
def index():
    global players_df
    return render_template(
        "index.html",
        player_names=sorted(list(players_df["name"])),
        attributes=list(players_df.columns),
    )


@application.route("/findSimilarities", methods=["POST"])
def findSimilarities():
    global players_df
    player = players_df[players_df["name"] == request.form["player_name"]].iloc[0]
    similar_players = findkNN(
        player,
        k=int(request.form["k"]),
        attributes_to_compare=json.loads(request.form["attributes"]),
    )
    return json.dumps(similar_players)


if __name__ == "__main__":
    loadData("./Data/Top5Leagues_201920_Stats.csv")
    application.run(host="0.0.0.0", debug=True)
