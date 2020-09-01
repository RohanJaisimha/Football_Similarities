import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import unidecode
import heapq
from flask import Flask, render_template, request
import json

application = Flask(__name__)

players_df = None

attacking_attributes = sorted(['shots_on_target_pct', 'goals_per90', 'assists_per90', 'pens_made_per90', 'pens_att_per90', 'xg_per90', 'npxg_per90', 'shots_total_per90', 'shots_on_target_per90', 'shots_free_kicks_per90', 'goals_per_shot_per90', 'goals_per_shot_on_target_per90', 'npxg_per_shot_per90', 'xg_net_per90', 'npxg_net_per90', 'offsides_per90'])
defensive_attributes = sorted(['dribble_tackles_pct', 'pressure_regain_pct', 'tackles_per90', 'tackles_won_per90', 'tackles_def_3rd_per90', 'tackles_mid_3rd_per90', 'tackles_att_3rd_per90', 'dribble_tackles_per90', 'dribbles_vs_per90', 'dribbled_past_per90', 'pressures_per90', 'pressure_regains_per90', 'pressures_def_3rd_per90', 'pressures_mid_3rd_per90', 'pressures_att_3rd_per90', 'blocks_per90', 'blocked_shots_per90', 'blocked_shots_saves_per90', 'blocked_passes_per90', 'interceptions_per90', 'clearances_per90', 'errors_per90', 'cards_yellow_red_per90', 'fouls_per90', 'pens_conceded_per90', 'own_goals_per90', 'ball_recoveries_per90', 'aerials_won_pct', 'aerials_won_per90', 'aerials_lost_per90'])
dribbling_attributes = sorted(['dribbles_completed_pct', 'dribbles_completed_per90', 'dribbles_per90', 'players_dribbled_past_per90', 'nutmegs_per90', 'fouled_per90', 'pens_won_per90', 'carries_per90', 'carry_distance_per90', 'carry_progressive_distance_per90', 'miscontrols_per90', 'dispossessed_per90', 'touches_per90', 'touches_def_pen_area_per90', 'touches_def_3rd_per90', 'touches_mid_3rd_per90', 'touches_att_3rd_per90', 'touches_att_pen_area_per90', 'touches_live_ball_per90'])
passing_attributes = sorted(['passes_pct', 'passes_pct_short', 'passes_pct_medium', 'passes_pct_long', 'passes_received_pct', 'xa_per90', 'passes_completed_per90', 'passes_per90', 'passes_total_distance_per90', 'passes_progressive_distance_per90', 'passes_completed_short_per90', 'passes_short_per90', 'passes_completed_medium_per90', 'passes_medium_per90', 'passes_completed_long_per90', 'passes_long_per90', 'xa_net_per90', 'assisted_shots_per90', 'passes_into_final_third_per90', 'passes_into_penalty_area_per90', 'crosses_into_penalty_area_per90', 'progressive_passes_per90', 'passes_live_per90', 'passes_dead_per90', 'passes_free_kicks_per90', 'through_balls_per90', 'passes_pressure_per90', 'passes_switches_per90', 'crosses_per90', 'corner_kicks_per90', 'corner_kicks_in_per90', 'corner_kicks_out_per90', 'corner_kicks_straight_per90', 'passes_ground_per90', 'passes_low_per90', 'passes_high_per90', 'passes_left_foot_per90', 'passes_right_foot_per90', 'passes_head_per90', 'throw_ins_per90', 'passes_other_body_per90', 'passes_offsides_per90', 'passes_oob_per90', 'passes_intercepted_per90', 'passes_blocked_per90', 'sca_per90', 'sca_passes_live_per90', 'sca_passes_dead_per90', 'sca_dribbles_per90', 'sca_shots_per90', 'sca_fouled_per90', 'gca_per90', 'gca_passes_live_per90', 'gca_passes_dead_per90', 'gca_dribbles_per90', 'gca_shots_per90', 'gca_fouled_per90', 'gca_og_for_per90', 'pass_targets_per90', 'passes_received_per90'])
discipline_attributes = sorted(['cards_yellow_per90', 'cards_red_per90'])

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
    if not attributes_to_compare:
        # if no attrbiutes are passed, use all of them
        attributes_to_compare = attacking_attributes + defensive_attributes + dribbling_attributes + passing_attributes + discipline_attributes

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
    while(i < k and i < len(players_df)):
        distance, player_name, squad = heapq.heappop(distances)
        if player_name == player["name"]:
            # the lowest distance to a player is always that player themselves,
            # so we can ignore that the first match
            i += 1
            continue
        score = round((1 - distance / len(attributes_to_compare)) * 100, 3)
        similar_players.append([player_name, squad, score])
        i += 1

    return similar_players


@application.route("/")
def index():
    global players_df

    player_names = sorted(list(players_df["name"]))
    overall_max_age = max(players_df["age"])
    overall_min_age = min(players_df["age"])

    return render_template(
        "index.html",
        player_names=player_names,
        attacking_attributes=attacking_attributes,
        defensive_attributes=defensive_attributes,
        dribbling_attributes=dribbling_attributes,
        passing_attributes=passing_attributes,
        discipline_attributes=discipline_attributes,
        overall_min_age=overall_min_age,
        overall_max_age=overall_max_age
    )


@application.route("/findSimilarities", methods=["POST"])
def findSimilarities():
    global players_df
    min_age, max_age = json.loads(request.form["age_range"])
    players_df = players_df[((players_df["age"] >= min_age) & (players_df["age"] <= max_age)) | (players_df["name"] == request.form["player_name"])]
    scaleData()
    player = players_df[players_df["name"] == request.form["player_name"]].iloc[0]
    similar_players = findkNN(
        player,
        k=int(request.form["k"]),
        attributes_to_compare=json.loads(request.form["attributes"]),
    )
    loadData("./Data/Top5Leagues_201920_Stats.csv")
    return json.dumps(similar_players)


loadData("./Data/Top5Leagues_201920_Stats.csv")

if __name__ == "__main__":
    application.run(debug=True)
