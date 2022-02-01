#! /usr/bin/env/python3

import f1db, pandas, plotly.graph_objects as go

with f1db.Connection() as conn:
    conn.execute_sql_script_file("standings_pretty.sql")
    df = pandas.read_sql_query("SELECT * FROM driver_standings_pretty", conn.connection)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x = df["round"], y = df["points"], color = df["code"]))

    fig.write_image("test.png", engine = "kaleido")