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
            figsize=(12, 8)
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
            frame_data = df.iloc[:i+1].iloc[-1].sort_values(ascending=True)
            frames.append(go.Frame(data=[go.Bar(
                x=frame_data.values,
                y=frame_data.index,
                orientation='h',
                text=frame_data.values,
                textposition='outside'
            )],
            layout=go.Layout(
                title=f"{title}<br>{df.index[i]}",
                xaxis=dict(range=[0, df.max().max() * 1.1]),
                yaxis=dict(categoryorder='total ascending')
            )))

        fig = go.Figure(
            data=[frames[0].data[0]],
            layout=go.Layout(
                title=title,
                updatemenus=[dict(
                    type="buttons",
                    buttons=[dict(label="再生",
                                  method="animate",
                                  args=[None, {"frame": {"duration": 100, "redraw": True},
                                               "fromcurrent": True,
                                               "transition": {"duration": 0}}])]
                )],
                xaxis=dict(range=[0, df.max().max() * 1.1]),
                yaxis=dict(categoryorder='total ascending')
            ),
            frames=frames
        )

        fig.update_layout(
            height=600,
            width=1000,
            **kwargs
        )
        
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
            values='Lines',
            color='changed_files',
            color_continuous_scale='RdBu',
            color_continuous_midpoint=np.average(df['changed_files']),
            hover_data=['date', 'Lines'],
            title=title
        )

        # Save the figure as an HTML file
        pio.write_html(fig, file=output_path)
        print(f"Treemap has been saved to {output_path}")