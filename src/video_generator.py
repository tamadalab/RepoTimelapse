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
    def generate_video(df, output_path, title):
        bcr.bar_chart_race(
            df=df,
            filename=output_path,
            title=title,
            steps_per_period=10,
            period_length=500,
            figsize=(12, 8),
        )

    @staticmethod
    def generate_plotly_animation(df, output_path, title, **kwargs):
        """
        Plotlyを使用してアニメーションを生成し、HTMLファイルとして保存します。

        :param df: 入力DataFrame
        :param output_path: 出力HTMLファイルのパス
        :param title: アニメーションのタイトル
        :param kwargs: Plotlyの追加パラメータ
        """
        frames = []
        for i in tqdm(range(len(df)), desc="フレーム生成中"):
            frame_data = df.iloc[: i + 1].iloc[-1].sort_values(ascending=True)
            frames.append(
                go.Frame(
                    data=[
                        go.Bar(
                            x=frame_data.values,
                            y=frame_data.index,
                            orientation="h",
                            text=frame_data.values,
                            textposition="outside",
                        )
                    ],
                    layout=go.Layout(
                        title=f"{title}<br>{df.index[i]}",
                        xaxis=dict(range=[0, df.max().max() * 1.1]),
                        yaxis=dict(categoryorder="total ascending"),
                    ),
                )
            )

        fig = go.Figure(
            data=[frames[0].data[0]],
            layout=go.Layout(
                title=title,
                updatemenus=[
                    dict(
                        type="buttons",
                        buttons=[
                            dict(
                                label="再生",
                                method="animate",
                                args=[
                                    None,
                                    {
                                        "frame": {"duration": 100, "redraw": True},
                                        "fromcurrent": True,
                                        "transition": {"duration": 0},
                                    },
                                ],
                            )
                        ],
                    )
                ],
                xaxis=dict(range=[0, df.max().max() * 1.1]),
                yaxis=dict(categoryorder="total ascending"),
            ),
            frames=frames,
        )

        fig.update_layout(height=600, width=1000, **kwargs)

        pio.write_html(fig, file=output_path, auto_play=False)
        print(f"アニメーションが {output_path} に保存されました")

    @staticmethod
    def generate_both(df, bar_chart_race_output, plotly_output, title):
        """
        bar_chart_raceとPlotly両方を使用してアニメーションを生成します。

        :param df: 入力DataFrame
        :param bar_chart_race_output: bar_chart_raceの出力ファイルパス
        :param plotly_output: Plotlyの出力HTMLファイルパス
        :param title: アニメーションのタイトル
        """
        VideoGenerator.generate_video(df, bar_chart_race_output, title)
        VideoGenerator.generate_plotly_animation(df, plotly_output, title)

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
    def prepare_treemap_data(df):
        """
        TreeMap用にデータを準備します

        :param df: 入力DataFrame
        :return: ids, parents, values, labels, customdataのタプル
        """
        # 全てのパスの部分を収集
        nodes = []
        root_added = False

        for _, row in df.iterrows():
            path_parts = row["File"].split("/")
            current_path = ""

            # ルートノードの追加（一度だけ）
            if not root_added:
                nodes.append(
                    {
                        "id": "root",
                        "parent": "",
                        "name": "root",
                        "full_path": "",
                        "lines": 0,
                        "changes": 0,
                        "type": "directory",
                    }
                )
                root_added = True

            # パスの各部分をノードとして追加
            for i, part in enumerate(path_parts):
                parent_path = current_path if current_path else "root"
                current_path = f"{current_path}/{part}".lstrip("/")

                # 最後の部分（ファイル自体）かどうかを判断
                is_file = i == len(path_parts) - 1 and row["Type"] == "file"

                node = {
                    "id": current_path,
                    "parent": parent_path,
                    "name": part,
                    "full_path": current_path,
                    "lines": row["Lines"] if is_file else 0,
                    "changes": row["changed_files"] if is_file else 0,
                    "type": "file" if is_file else "directory",
                }
                nodes.append(node)

        # ノードの重複を除去（同じIDのノードは最新のものを保持）
        unique_nodes = {}
        for node in nodes:
            unique_nodes[node["id"]] = node

        # データの準備
        ids = [node["id"] for node in unique_nodes.values()]
        parents = [node["parent"] for node in unique_nodes.values()]
        values = [node["lines"] for node in unique_nodes.values()]
        labels = [node["name"] for node in unique_nodes.values()]
        customdata = np.array(
            [
                [node["full_path"], node["lines"], node["changes"], node["type"]]
                for node in unique_nodes.values()
            ]
        )

        return ids, parents, values, labels, customdata

    @staticmethod
    def generate_animated_treemap(period_dfs, output_path, title):
        """
        時系列のTreeMapアニメーションを生成します

        :param period_dfs: 期間ごとのDataFrameを含む辞書
        :param output_path: 出力するHTMLファイルのパス
        :param title: グラフのタイトル
        """
        frames = []
        max_changes = max(
            df["changed_files"].max()
            for df in period_dfs.values()
            if not df.empty and "changed_files" in df.columns
        )

        # 初期フレームのデータを取得
        first_df = next(iter(period_dfs.values()))
        ids, parents, values, labels, customdata = VideoGenerator.prepare_treemap_data(
            first_df
        )

        # 基本のTreemapを作成
        fig = go.Figure(
            data=[
                go.Treemap(
                    ids=ids,
                    parents=parents,
                    values=values,
                    labels=labels,
                    customdata=customdata,
                    hovertemplate="""
                    <b>Path:</b> %{customdata[0]}<br>
                    <b>Lines:</b> %{customdata[1]}<br>
                    <b>Changes:</b> %{customdata[2]}<br>
                    <b>Type:</b> %{customdata[3]}
                    <extra></extra>
                """,
                    textinfo="label",
                    marker=dict(
                        colors=customdata[:, 2],  # changes as color
                        colorscale="blues",
                        cmid=max_changes / 2,
                        showscale=True,
                        colorbar=dict(title="Number of Changes"),
                    ),
                )
            ]
        )

        # フレームの生成
        for date, df in tqdm(period_dfs.items(), desc="Generating frames"):
            if not df.empty:
                ids, parents, values, labels, customdata = (
                    VideoGenerator.prepare_treemap_data(df)
                )

                frame = go.Frame(
                    data=[
                        go.Treemap(
                            ids=ids,
                            parents=parents,
                            values=values,
                            labels=labels,
                            customdata=customdata,
                            hovertemplate="""
                            <b>Path:</b> %{customdata[0]}<br>
                            <b>Lines:</b> %{customdata[1]}<br>
                            <b>Changes:</b> %{customdata[2]}<br>
                            <b>Type:</b> %{customdata[3]}
                            <extra></extra>
                        """,
                            textinfo="label",
                            marker=dict(
                                colors=customdata[:, 2],
                                colorscale="blues",
                                cmid=max_changes / 2,
                            ),
                        )
                    ],
                    name=date.strftime("%Y-%m-%d"),
                )
                frames.append(frame)

        # アニメーションの設定
        fig.frames = frames

        # レイアウトの設定
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sup>Color indicates number of changes</sup>",
                x=0.5,
                xanchor="center",
            ),
            width=1200,
            height=800,
            updatemenus=[
                {
                    "type": "buttons",
                    "showactive": False,
                    "y": 1.2,
                    "x": 0.1,
                    "xanchor": "right",
                    "yanchor": "top",
                    "buttons": [
                        dict(
                            label="Play",
                            method="animate",
                            args=[
                                None,
                                {
                                    "frame": {"duration": 1000, "redraw": True},
                                    "fromcurrent": True,
                                    "transition": {"duration": 500},
                                },
                            ],
                        ),
                        dict(
                            label="Pause",
                            method="animate",
                            args=[
                                [None],
                                {
                                    "frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                    "transition": {"duration": 0},
                                },
                            ],
                        ),
                    ],
                }
            ],
            sliders=[
                {
                    "currentvalue": {"prefix": "Date: ", "xanchor": "right"},
                    "pad": {"t": 50},
                    "len": 0.9,
                    "x": 0.1,
                    "y": 0,
                    "steps": [
                        {
                            "label": frame.name,
                            "method": "animate",
                            "args": [
                                [frame.name],
                                {
                                    "frame": {"duration": 1000, "redraw": True},
                                    "transition": {"duration": 500},
                                    "mode": "immediate",
                                },
                            ],
                        }
                        for frame in frames
                    ],
                }
            ],
        )

        # HTMLファイルとして保存
        pio.write_html(fig, file=output_path)
        print(f"Animated treemap has been saved to {output_path}")

    @staticmethod
    def bar_chart(df, output_path):
        fig = px.bar(
            df, x=df["extension"], y=df["size"], log_y=True, title="File Extensions"
        )
        fig.update_layout(
            xaxis=dict(
                tickangle=-45,  # x軸ラベルを45度回転
                tickmode="array",
                tickvals=list(range(len(df["extension"]))),
                ticktext=df["extension"].tolist(),
            ),
            bargap=0.2,  # 棒グラフ間のギャップを調整
            height=600,  # グラフの高さを調整
            margin=dict(b=100),  # 下部のマージンを増やしてラベルの表示を確保
        )

        pio.write_html(fig, file=output_path)
