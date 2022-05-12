#! /usr/bin/env/python3
# pylint: disable = missing-module-docstring

import f1db, pandas, plotly.graph_objects as go
import logging
from tqdm import tqdm

f1db.logger.setLevel(logging.INFO)

DESIRED_NUM_TICKS = 10 # This represents the number of y-axis ticks you'd ideally like to have.
DTICK_ROUND_TARGET = 5 # This represents the the "round to the nearest X" target for the y-axis tick increment.

X_AXIS_OFFSET_MULTIPLIER = 0.022
ANNOTATION_OFFSET_MULTIPLIER = 0.007

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

def calculate_x_range(min_x_value, max_x_value): # pylint: disable = missing-function-docstring
    base_offset = max_x_value * X_AXIS_OFFSET_MULTIPLIER
    return [
        min_x_value + (base_offset * -1.5),
        max_x_value + base_offset
    ]

def calculate_annotation_offset(max_x_value): # pylint: disable = missing-function-docstring
    return max_x_value * ANNOTATION_OFFSET_MULTIPLIER

def calculate_dtick(max_value):
    '''This calculates the "dtick" (the value between each tick) for a chart's y-axis.
    Essentially, this divides the max value on the y-axis by the desired number of
    y-axis ticks, then rounds it to the desired level of precision.'''
    return DTICK_ROUND_TARGET * round((max_value / DESIRED_NUM_TICKS) / DTICK_ROUND_TARGET)

def create_rgba_from_hex(hex_code, opacity_percent = 1): # pylint: disable = missing-function-docstring
    sh = hex_code.lstrip("#")
    rgb_tuple = tuple(int(sh[i:i + 2], base = 16) for i in (0, 2, 4))
    return f"rgba({rgb_tuple[0]!s},{rgb_tuple[1]!s},{rgb_tuple[2]!s},{opacity_percent!s})"

def export_driver_standings_figure(conn, **sql_kwargs): # pylint: disable = missing-function-docstring
    conn.execute_sql_script_file("standings_pretty.sql", **sql_kwargs)
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    figure = go.Figure(layout = DEFAULT_LAYOUT)
    figure.update_layout(
        title = {"text": f"{df['year'].tolist()[0]} World Drivers' Championship Standings by Grand Prix"},
        xaxis = {
            "categoryorder": "array",
            "categoryarray": df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist(),
            "range": calculate_x_range(0, df["round"].nunique() - 1)
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
        annotation_offset = calculate_annotation_offset(df["round"].nunique() - 1)
        if drive_constants["is_first_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "right",
                "x": (drive_df.iloc[0]["round"] - 1) - annotation_offset,
                "y": drive_df.iloc[0]["position"]
            })
        if drive_constants["is_final_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "left",
                "x": (drive_df.iloc[-1]["round"] - 1) + annotation_offset,
                "y": drive_df.iloc[-1]["position"]
            })

    figure.update_layout(annotations = annotations)

    figure.write_image(f"driver_standings_{drive_constants['year']!s}.png", engine = "kaleido")

def export_driver_points_figure(conn, **sql_kwargs): # pylint: disable = missing-function-docstring
    conn.execute_sql_script_file("standings_pretty.sql", **sql_kwargs)
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    figure = go.Figure(layout = DEFAULT_LAYOUT)
    figure.update_layout(
        title = {"text": f"{df['year'].tolist()[0]} World Drivers' Championship Points by Grand Prix"},
        xaxis = {
            "categoryorder": "array",
            "categoryarray": df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist(),
            "range": calculate_x_range(0, df["round"].nunique() - 1)
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
        annotation_offset = calculate_annotation_offset(df["round"].nunique() - 1)
        if drive_constants["is_first_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "right",
                "x": (drive_df.iloc[0]["round"] - 1) - annotation_offset,
                "y": drive_df.iloc[0]["points"]
            })
        if drive_constants["is_final_drive"]:
            annotations.append(annotation_base | {
                "xanchor": "left",
                "x": (drive_df.iloc[-1]["round"] - 1) + annotation_offset,
                "y": drive_df.iloc[-1]["points"]
            })

    figure.update_layout(annotations = annotations)
    figure.write_image(f"driver_points_{drive_constants['year']!s}.png", engine = "kaleido")

def export_lap_positions_figure(conn, **sql_kwargs): # pylint: disable = missing-function-docstring
    conn.execute_sql_script_file("lap_position_chart.sql", **sql_kwargs)
    df = pandas.read_sql_query("SELECT * FROM lap_position_chart", conn.connection)

    figure = go.Figure(layout = DEFAULT_LAYOUT)
    figure.update_layout(
        title = {"text": f"{df['year'].tolist()[0]} {df['race_name'].tolist()[0]}"},
        xaxis = {
            "range": calculate_x_range(0, df["lap"].max()),
            "dtick": calculate_dtick(df["lap"].max()),
            "tickangle": 0
        },
        yaxis = {
            "title_text": "Position",
            "range": [df["driver_id"].nunique() + 0.5, 0.5],
            "tick0": 1,
            "dtick": 1
        }
    )

    #breakpoint()

    annotations = []

    for driver_id in df["driver_id"].drop_duplicates():
        driver_df = df.query(f"driver_id == {driver_id!s}")
        driver_constants = driver_df.iloc[0]

        figure.add_trace(go.Scatter(
            name = f"{driver_constants['surname']} ({driver_constants['constructor_name']})",
            x = driver_df["lap"],
            y = driver_df["position"],
            mode = "lines+markers",
            connectgaps = False,
            legendrank = driver_constants["legend_rank"],
            line = {
                "width": 3,
                "color": driver_constants["hex_code"],
                "dash": DRIVER_RANK_LINE_TYPES[driver_constants["team_driver_rank"]]
            }
        ))

        driver_pitstops_df = driver_df.query("marker_type == 'Pitted'")
        figure.add_trace(go.Scatter(
            name = f"{driver_constants['full_name']} - Pit Stops",
            x = driver_pitstops_df["lap"],
            y = driver_pitstops_df["position"],
            mode = "markers",
            showlegend = False,
            marker = {
                "size": 15,
                "color": "#FF0000",
                "line": {"color": "#000000", "width": 2},
                "symbol": "octagon"
            }
        ))

        driver_retirements_df = driver_df.query("marker_type == 'Retired'")
        figure.add_trace(go.Scatter(
            name = f"{driver_constants['full_name']} - Pit Stops",
            x = driver_retirements_df["lap"] - 1,
            y = driver_retirements_df["previous_lap_position"],
            mode = "markers",
            showlegend = False,
            marker = {
                "size": 20,
                "color": driver_constants["hex_code"],
                "symbol": "x"
            }
        ))

        annotation_base = {"text": driver_constants["code"], "showarrow": False, "font": {"size": 14}}
        annotation_offset = calculate_annotation_offset(df["lap"].max())
        annotations.append(annotation_base | {
            "xanchor": "right",
            "x": driver_df.iloc[0]["lap"] - annotation_offset,
            "y": driver_df.iloc[0]["position"]
        })
        annotations.append(annotation_base | {
            "xanchor": "left",
            "x": driver_df.iloc[-1]["lap"] + annotation_offset,
            "y": driver_df.iloc[-1]["position"]
        })

    figure.update_layout(annotations = annotations)
    figure.write_image(f"lap_positions_{driver_constants['year']!s}_{driver_constants['race_short_name'].replace(' ', ' ').lower()!s}.png", engine = "kaleido")

def export_delta_standings_figure(conn, **sql_kwargs): # pylint: disable = missing-function-docstring
    conn.execute_sql_script_file("delta_standings_boxplot.sql", **sql_kwargs)
    df = pandas.read_sql_query("SELECT * FROM delta_standings_boxplot", conn.connection)
    base_offset = df["current_position"].max() * X_AXIS_OFFSET_MULTIPLIER

    figure = go.Figure(layout = DEFAULT_LAYOUT)
    figure.update_layout(
        title = {"text": (
            f"Potential Standings Changes After the {df['year'].tolist()[0]} {df['race_name'].tolist()[0]}<br>"
            f"<sup><i>The left and right ends of the 'box' and 'whiskers' are the best/worst positions attainable at the end of the next Grand Prix and the end of this season, respectively."
            #f"The left and right ends of the 'box' are the best/worst positions attainable after the end of the next Grand Prix.<br>"
            #f"The vertical line within the box represents this driver's current position. This might overlap with one end of the box."
            f"</i></sup>"
        )},
        xaxis = {
            "title_text": "Possible Future Positions",
            "title_font": {"size": 16},
            "gridwidth": 0.5,
            "gridcolor": "#BBBBBB",
            "range": [-2.5, df["current_position"].max() + base_offset],
            "tickvals": list(range(1, df["current_position"].max() + 1)),
            "tickangle": 0
        },
        yaxis = {
            "title_text": "Current Position",
            "range": [df["current_position"].max() + base_offset, 1 - base_offset],
            "tick0": 1,
            "dtick": 1,
            "gridcolor": "#FFFFFF"
        }
    )

    annotations = []

    for driver_id in df["driver_id"].drop_duplicates():
        driver_df = df.query(f"driver_id == {driver_id!s}")

        #breakpoint()
        driver_constants = driver_df.iloc[0]

        figure.add_trace(go.Box(
            name = driver_constants["full_name"],
            y0 = driver_constants["current_position"],

            lowerfence = driver_df["best_position_this_season"],
            q1 = driver_df["best_position_next_race"],
            median = driver_df["current_position"],
            q3 = driver_df["worst_position_next_race"],
            upperfence = driver_df["worst_position_this_season"],
            showlegend = False,
            orientation = "h",
            line = {
                "width": 3,
                "color": driver_constants["hex_code"]
            },
            fillcolor = create_rgba_from_hex(driver_constants["hex_code"], 0.25),
            whiskerwidth = 1
        ))

        annotation_offset = calculate_annotation_offset(df["current_position"].max())
        annotations.append({
            "text": f"{driver_constants['full_name']} ({driver_constants['constructor_name']}) - {round(driver_constants['current_points'])} pts",
            "xanchor": "right",
            "x": 1 - annotation_offset,
            "y": driver_df.iloc[0]["current_position"],
            "showarrow": False,
            "font": {"size": 14}
        })

    figure.update_layout(annotations = annotations)
    figure.write_image(f"delta_standings_{driver_constants['year']!s}_{driver_constants['race_short_name'].replace(' ', ' ').lower()!s}.png", engine = "kaleido")

if __name__ == "__main__":
    with f1db.Connection() as connection:
        export_delta_standings_figure(connection, race_id = 1076)
        for year in tqdm([2022]):
            export_driver_standings_figure(connection, year = year)
            export_driver_points_figure(connection, year = year)
        for race_id in tqdm([1074, 1075, 1076, 1077, 1078]):
            export_lap_positions_figure(connection, race_id = race_id)
            export_delta_standings_figure(connection, race_id = race_id)