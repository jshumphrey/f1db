#! /usr/bin/env/python3
# pylint: disable = missing-module-docstring

import f1db, pandas, plotly.graph_objects as go
import logging
from tqdm import tqdm

f1db.logger.setLevel(logging.INFO)

DESIRED_NUM_TICKS = 10 # This represents the number of y-axis ticks you'd ideally like to have.
DTICK_ROUND_TARGET = 5 # This represents the the "round to the nearest X" target for the y-axis tick increment.

DEFAULT_LAYOUT = go.Layout(
    width = 1920,
    height = 1080,
    paper_bgcolor = "#FFFFFF",
    plot_bgcolor = "#FFFFFF",
    title = {
        "text": "Placeholder",
        "font": {"size": 25},
        "x": 0.5,
        "xanchor": "center"
    },
    xaxis = {
        "zeroline": False,
        "tickangle": -45
    },
    yaxis = {
        "title_text": "Placeholder",
        "title_font": {"size": 16},
        "zeroline": False,
        "gridwidth": 0.5,
        "gridcolor": "#BBBBBB"
    }
)

DRIVER_RANK_LINE_TYPES = {
    0: "solid",
    1: "solid",
    2: "dash",
    3: "dot",
    4: "dot",
    5: "dot"
}

def calculate_dtick(max_value):
    '''This calculates the "dtick" (the value between each tick) for a chart's y-axis.
    Essentially, this divides the max value on the y-axis by the desired number of
    y-axis ticks, then rounds it to the desired level of precision.'''
    return DTICK_ROUND_TARGET * round((max_value / DESIRED_NUM_TICKS) / DTICK_ROUND_TARGET)

def export_driver_standings_figure(conn, **sql_kwargs): # pylint: disable = missing-function-docstring
    conn.execute_sql_script_file("standings_pretty.sql", **sql_kwargs)
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    figure = go.Figure(layout = DEFAULT_LAYOUT)
    figure.update_layout(
        title = {"text": f"{df['year'].tolist()[0]} World Drivers' Championship Standings by Grand Prix"},
        xaxis = {
            "categoryorder": "array",
            "categoryarray": df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist(),
            "range": [-0.75, df["round"].nunique() - 0.5]
        },
        yaxis = {
            "title_text": "WDC Standings Position",
            "range": [df["driver_id"].nunique() + 0.5, 0.5],
            "tick0": 1,
            "dtick": 1
        }
    )

    drives_df = df[["driver_id", "drive_id"]].drop_duplicates()

    #breakpoint()

    annotations = []

    for driver_id, drive_id in zip(drives_df["driver_id"], drives_df["drive_id"]):
        drive_df = df.query(f"driver_id == {driver_id!s} & drive_id == {drive_id!s}")
        drive_constants = drive_df.iloc[0]

        figure.add_trace(go.Scatter(
            name = f"{drive_constants['surname']} ({drive_constants['constructor_name']})",
            x = drive_df["race_name"],
            y = drive_df["position"],
            mode = "lines+markers",
            connectgaps = False,
            legendrank = drive_constants["legend_rank"],
            line = {
                "width": 3,
                "color": drive_constants["hex_code"],
                "dash": DRIVER_RANK_LINE_TYPES[drive_constants["team_driver_rank"]]
            }
        ))

        annotation_base = {"text": drive_constants["code"], "showarrow": False, "font": {"size": 14}}
        if drive_constants["is_first_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "right",
                "x": (drive_df.iloc[0]["round"] - 1) - 0.2,
                "y": drive_df.iloc[0]["position"]
            })
        if drive_constants["is_final_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "left",
                "x": (drive_df.iloc[-1]["round"] - 1) + 0.2,
                "y": drive_df.iloc[-1]["position"]
            })

    figure.update_layout(annotations = annotations)

    figure.write_image(f"driver_standings_{drive_constants['year']!s}.png", engine = "kaleido")

def export_driver_points_figure(conn, **sql_kwargs): # pylint: disable = missing-function-docstring
    conn.execute_sql_script_file("standings_pretty.sql", **sql_kwargs)
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    num_races = df["round"].nunique()

    figure = go.Figure(layout = DEFAULT_LAYOUT)
    figure.update_layout(
        title = {"text": f"{df['year'].tolist()[0]} World Drivers' Championship Points by Grand Prix"},
        xaxis = {
            "categoryorder": "array",
            "categoryarray": df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist(),
            "range": [-0.75, num_races - 0.5]
        },
        yaxis = {
            "title_text": "WDC Points",
            "range": [0, df["points"].max() * 1.05],
            "tick0": 0,
            "dtick": calculate_dtick(df["points"].max())
        }
    )

    drives_df = df[["driver_id", "drive_id"]].drop_duplicates()

    #breakpoint()

    annotations = []

    for driver_id, drive_id in zip(drives_df["driver_id"], drives_df["drive_id"]):
        drive_df = df.query(f"driver_id == {driver_id!s} & drive_id == {drive_id!s}")
        drive_constants = drive_df.iloc[0]

        figure.add_trace(go.Scatter(
            name = f"{drive_constants['surname']} ({drive_constants['constructor_name']})",
            x = drive_df["race_name"],
            y = drive_df["points"],
            mode = "lines+markers",
            connectgaps = False,
            legendrank = drive_constants["legend_rank"],
            line = {
                "width": 3,
                "color": drive_constants["hex_code"],
                "dash": DRIVER_RANK_LINE_TYPES[drive_constants["team_driver_rank"]]
            }
        ))

        annotation_base = {"text": drive_constants["code"], "showarrow": False, "font": {"size": 14}}
        if drive_constants["is_first_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "right",
                "x": (drive_df.iloc[0]["round"] - 1) - 0.2,
                "y": drive_df.iloc[0]["points"]
            })
        if drive_constants["is_final_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "left",
                "x": (drive_df.iloc[-1]["round"] - 1) + 0.2,
                "y": drive_df.iloc[-1]["points"]
            })

    figure.update_layout(annotations = annotations)

    figure.write_image(f"driver_points_{drive_constants['year']!s}.png", engine = "kaleido")

if __name__ == "__main__":
    with f1db.Connection() as connnection:
        for year in tqdm([2002, 2007, 2021, 2022]):
            export_driver_standings_figure(connnection, year = year)
            export_driver_points_figure(connnection, year = year)