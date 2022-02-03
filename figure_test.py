#! /usr/bin/env/python3
# pylint: disable = missing-module-docstring

import f1db, pandas, plotly.graph_objects as go
import pdb # pylint: disable = unused-import

with f1db.Connection() as conn:
    conn.execute_sql_script_file("standings_pretty.sql")
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    # Points
    points_fig = go.Figure()
    points_fig.update_layout (
        width = 1920,
        height = 1080
    )
    points_fig.update_xaxes(
        tickangle = -45
    )

    for driver in df["code"].unique().tolist():
        driver_df = df.query(f"code == '{driver}'")
        line_dict = {"color": driver_df["hex_code"].tolist()[0]}
        team_driver_rank = driver_df["team_driver_rank"].tolist()[0]
        if team_driver_rank > 1:
            line_dict["dash"] = "dash" if team_driver_rank == 2 else "dot"

        points_fig.add_trace(go.Scatter(
            name = driver,
            x = driver_df["race_name"],
            y = driver_df["points"],
            mode = "lines+markers",
            connectgaps = False,
            line = line_dict
        ))

    points_fig.update_xaxes(
        categoryorder = 'array',
        categoryarray = df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist()
    )

    points_fig.write_image("points.png", engine = "kaleido")

    # Position
    position_fig = go.Figure()
    position_fig.update_layout (
        width = 1920,
        height = 1080,
        paper_bgcolor = "#FFFFFF",
        plot_bgcolor = "#FFFFFF",
        title = {
            "text": f"{df['year'].tolist()[0]} World Drivers' Championship Standings by Grand Prix",
            "font": {"size": 25},
            "x": 0.5,
            "xanchor": "center"
        }
    )
    position_fig.update_xaxes(
        zeroline = False,
        tickangle = -45
    )
    position_fig.update_yaxes(
        title_text = "WDC Standings Position",
        title_font = {"size": 16},
        zeroline = False,
        gridwidth = .5,
        gridcolor = "#BBBBBB"
    )

    pdb.set_trace()

    for driver in df["code"].unique().tolist():
        driver_df = df.query(f"code == '{driver}'")
        line_dict = {
            "color": driver_df["hex_code"].tolist()[0],
            "width": 3
        }
        team_driver_rank = driver_df["team_driver_rank"].tolist()[0]
        if team_driver_rank > 1:
            line_dict["dash"] = "dash" if team_driver_rank == 2 else "dot"

        position_fig.add_trace(go.Scatter(
            name = driver,
            x = driver_df["race_name"],
            y = driver_df["position"],
            mode = "lines+markers",
            connectgaps = False,
            line = line_dict
        ))

    position_fig.update_xaxes(
        categoryorder = 'array',
        categoryarray = df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist()
    )
    position_fig.update_yaxes(
        range = [len(position_fig.data) + 0.5, 0.5],
        tick0 = 1,
        dtick = 1,
    )

    position_fig.update_layout(
        annotations = [{
            "x": position_fig.layout["xaxis"]["categoryarray"].index(trace["x"][0]) - 0.25,
            "y": trace["y"][0],
            "xanchor": "right",
            "text": trace["name"],
            "showarrow": False,
            "font": {"size": 14}
        } for trace in position_fig.data]
        + [{
            "x": position_fig.layout["xaxis"]["categoryarray"].index(trace["x"][-1]) + 0.25,
            "y": trace["y"][-1],
            "xanchor": "left",
            "text": trace["name"],
            "showarrow": False,
            "font": {"size": 14}
        } for trace in position_fig.data]
    )

    position_fig.write_image("position.png", engine = "kaleido")