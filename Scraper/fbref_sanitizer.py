import pandas as pd
from fbref_constants import *


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
    columns_to_drop = [column for column in df.columns if "90" in column]
    df = df.drop(columns_to_drop, axis=1)
    return df


def removeMatchesColumns(df):
    columns_to_drop = [column for column in df.columns if column.startswith("Matches")]
    df = df.drop(columns_to_drop, axis=1)
    return df


def removeSquadTotalAndOpponentTotal(df):
    df = df[(df["Player"] != "Squad Total") & (df["Player"] != "Opponent Total")]
    return df


def cleanAgeAndNation(df):
    ages = []
    nations = []
    for i in range(len(df)):
        if not pd.isnull(df.iloc[i]["Age"]) and not isNumeric(df.iloc[i]["Age"]):
            ages.append(df.iloc[i]["Age"].split("-")[0])
        else:
            ages.append(None)
        if not pd.isnull(df.iloc[i]["Nation"]):
            nations.append(df.iloc[i]["Nation"].split()[-1])
        else:
            nations.append(None)

    df["Age"] = ages
    df["Nation"] = nations
    return df


def removeUnwantedColumns(df):
    df = df.drop(UNWANTED_COLUMNS, axis=1)
    return df


def renameColumns(df):
    df = df.rename(columns=COLUMNS_RENAMING_MAP)
    return df


def main():
    df = pd.read_csv(FILENAME)

    print(df.shape)

    df = removeP90Columns(df)
    df = removeMatchesColumns(df)
    df = removeUnwantedColumns(df)
    df = removeSquadTotalAndOpponentTotal(df)
    df = removeGoalkeepers(df)
    df = cleanAgeAndNation(df)
    df = renameColumns(df)

    print(df.shape)

    df.to_csv(FILENAME, index=False)


if __name__ == "__main__":
    main()
