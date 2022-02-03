#! /usr/bin/env/python3
# pylint: disable = missing-module-docstring

import f1db, pandas, plotly.graph_objects as go
import logging
import pdb # pylint: disable = unused-import

f1db.logger.setLevel(logging.INFO)

with f1db.Connection() as conn:
    conn.execute_sql_script_file("standings_pretty.sql")
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    # Points
    #points_fig = go.Figure()
    #points_fig.update_layout (
    #    width = 1920,
    #    height = 1080
    #)
    #points_fig.update_xaxes(
    #    tickangle = -45
    #)

    #for driver in df["code"].unique().tolist():
    #    driver_df = df.query(f"code == '{driver}'")
    #    line_dict = {"color": driver_df["hex_code"].tolist()[0]}
    #    team_driver_rank = driver_df["team_driver_rank"].tolist()[0]
    #    if team_driver_rank > 1:
    #        line_dict["dash"] = "dash" if team_driver_rank == 2 else "dot"

    #    points_fig.add_trace(go.Scatter(
    #        name = driver,
    #        x = driver_df["race_name"],
    #        y = driver_df["points"],
    #        mode = "lines+markers",
    #        connectgaps = False,
    #        line = line_dict
    #    ))

    #points_fig.update_xaxes(
    #    categoryorder = 'array',
    #    categoryarray = df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist()
    #)

    #points_fig.write_image("points.png", engine = "kaleido")

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

    drives_df = df[["driver_id", "drive_id"]].drop_duplicates()

    #pdb.set_trace()

    annotations = []

    for driver_id, drive_id in zip(drives_df["driver_id"], drives_df["drive_id"]):
        drive_df = df.query(f"driver_id == {driver_id!s} & drive_id == {drive_id!s}")
        drive_constants = drive_df.iloc[0]

        line_dict = {"color": drive_constants["hex_code"], "width": 3}
        if drive_constants["team_driver_rank"] > 1:
            line_dict["dash"] = "dash" if drive_constants["team_driver_rank"] == 2 else "dot"

        position_fig.add_trace(go.Scatter(
            name = f"{drive_constants['surname']} ({drive_constants['constructor_name']})",
            x = drive_df["race_name"],
            y = drive_df["position"],
            mode = "lines+markers",
            connectgaps = False,
            line = line_dict,
            legendrank = drive_constants["legend_rank"]
        ))

        for endpoint in [0, 1]:
            if (
                (not endpoint and drive_constants["is_first_drive"])
                or (endpoint and drive_constants["is_final_drive"])
            ):
                annotations.append({
                    "x": (drive_df.iloc[endpoint * -1]["round"] - 1) + (0.2 * (-1 if not endpoint else 1)),
                    "y": drive_df.iloc[endpoint * -1]["position"],
                    "xanchor": "right" if not endpoint else "left",
                    "text": drive_constants["code"],
                    "showarrow": False,
                    "font": {"size": 14}
                })

    position_fig.update_xaxes(
        categoryorder = 'array',
        categoryarray = df[["round", "race_name"]].drop_duplicates().sort_values("round")["race_name"].tolist(),
        range = [-0.75, df["round"].nunique() - 0.5]
    )
    position_fig.update_yaxes(
        range = [df["driver_id"].nunique() + 0.5, 0.5],
        tick0 = 1,
        dtick = 1,
    )

    position_fig.update_layout(annotations = annotations)

    position_fig.write_image("position.png", engine = "kaleido")