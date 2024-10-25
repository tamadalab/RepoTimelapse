import bar_chart_race as bcr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from tqdm import tqdm
import plotly.io as pio
import plotly.express as px
import numpy as np


class VideoGenerator:
    @staticmethod
    def generate_treemap(df, output_path, title, path_columns):
        """
        Generates a treemap visualization using Plotly and saves it as an HTML file.

        :param df: DataFrame containing the data
        :param output_path: Path to save the HTML file
        :param title: Title of the treemap
        :param path_columns: List of column names to use for the treemap hierarchy
        """
        fig = px.treemap(
            df,
            path=path_columns,
            values="Lines",
            color="changed_files",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=np.average(df["changed_files"]),
            hover_data=["date", "Lines"],
            title=title,
        )

        # Save the figure as an HTML file
        pio.write_html(fig, file=output_path)
        print(f"Treemap has been saved to {output_path}")

    @staticmethod
    def create_path_columns(df):
        path_parts = df["path"].str.split("/", expand=True)
        for i in range(len(path_parts.columns)):
            df[f"path{i}"] = path_parts[i]

        # 動的にパスカラムのリストを作成
        return [f"path{i}" for i in range(len(path_parts.columns))]

    @staticmethod
    def generate_extend_treemap(df, output_path):
        commit0 = df["commit_hash"].iloc[0]
        commits = df["commit_hash"].unique()

        # Make a list of frame
        frame0 = None
        frames = []
        for commit in commits:
            df_tmp = df[df["commit_hash"] == commit]
            treemap = go.Treemap(
                ids=df_tmp["path"],
                labels=df_tmp["name"],
                values=df_tmp["size"],
                parents=df_tmp["parent"],
                branchvalues="total",
                # pathbar_textfont_size=15,
                root_color="lightgrey",
                # textinfo = "label+value+percent parent",
                # texttemplate='%{label} <br> %{value} tonnes <br> %{percentRoot}'
            )
            if frame0 is None:
                frame0 = treemap
            frames.append(go.Frame(name=f"frame-{commit}", data=treemap))
        # Make sliders
        sliders = [
            dict(
                steps=[
                    dict(
                        method="animate",
                        args=[
                            [f"frame-{commit}"],
                            dict(
                                mode="e",
                                frame=dict(redraw=True),
                                transition=dict(duration=200),
                            ),
                        ],
                        label=f"{commit}",
                    )
                    for commit in commits
                ],
                transition=dict(duration=0),
                x=0,
                y=0,
                currentvalue=dict(
                    font=dict(size=12),
                    prefix="Commit: ",
                    visible=True,
                    xanchor="center",
                ),
                len=1.0,
                active=1,
            )
        ]
        # create the layout object with slider parameters
        layout = {
            "title": f"Treemap of {commit0}",
            "xaxis": {"visible": True, "showline": True},
            "yaxis": {"type": "log", "visible": True, "showline": True},
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "method": "animate",
                            "label": "play",
                            "args": [
                                None,
                                dict(
                                    frame=dict(duration=600, redraw=True),
                                    transition=dict(duration=200),
                                    fromcurrent=True,
                                    mode="immediate",
                                ),
                            ],
                        }
                    ],
                }
            ],
            "sliders": sliders,
        }
        # Create the final figure with layout and frame parameters
        figure = go.Figure(data=frame0, layout=layout, frames=frames)
        # Save the figure as an HTML file
        pio.write_html(figure, file=output_path)

        figure.show()

    @staticmethod
    def bar_chart(df, output_path):
        fig = px.bar(
            df, x=df["extension"], y=df["size"], log_y=True, title="File Extensions"
        )
        fig.update_layout(
        xaxis=dict(
            tickangle=-45,  # x軸ラベルを45度回転
            tickmode='array',
            tickvals=list(range(len(df['extension']))),
            ticktext=df['extension'].tolist()
        ),
        bargap=0.2,  # 棒グラフ間のギャップを調整
        height=600,  # グラフの高さを調整
        margin=dict(b=100)  # 下部のマージンを増やしてラベルの表示を確保
)


        pio.write_image(fig, file="out/stleary/JSON-java/bar_chart.pdf")
        pio.write_html(fig, file=output_path)

    @staticmethod
    def pie_chart(df, output_path):
        fig = px.pie(df, values="size", names="extension", title="File Extensions")
        pio.write_html(fig, file=output_path)

    @staticmethod
    def total_line_count(df, output_path):
        fig = px.line(df, x=df['date'], y=df['total_lines'], title="Total Line Count")
        pio.write_html(fig, file=output_path)

    @staticmethod
    def file_count(df, output_path):
        fig = px.line(df, x=df['date'], y=df['files'], title="File Count")
        pio.write_html(fig, file=output_path)
