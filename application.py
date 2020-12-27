import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import heapq
from flask import Flask, render_template
import json
import os
import re
from constants import *

# import difflib
from fuzzywuzzy.fuzz import partial_ratio

application = Flask(__name__)


@application.route("/")
def home():
    seasons = map(lambda s: re.search("\d+-\d+", s).group(), os.listdir("./Data"))
    return render_template(
        "home.html",
        seasons=seasons,
    )


@application.route("/similarities/<season>", methods=["GET"])
def similarities(season):
    filename = "./Data/Top5Leagues_{}.csv".format(season)
    df = pd.read_csv(filename)
    return render_template(
        "similarities.html",
        ATTRIBUTES=ATTRIBUTES,
        positions=["DF", "MF", "FW"],
    )


if __name__ == "__main__":
    application.run(debug=True, port=5000, host="0.0.0.0")
