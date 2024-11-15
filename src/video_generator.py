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

    @staticmethod
    def prepare_treemap_data(df):
        """
        TreeMap用にデータを準備します
        
        :param df: 入力DataFrame
        :return: TreeMap用に処理されたDataFrame
        """
        # 全てのパスの部分を収集
        all_paths = []
        for _, row in df.iterrows():
            path_parts = row['path_parts']
            current_path = ''
            for part in path_parts:
                parent_path = current_path
                current_path = f"{current_path}/{part}".lstrip('/')
                all_paths.append({
                    'id': current_path,
                    'parent': parent_path or '/',
                    'name': part,
                    'Lines': row['Lines'] if current_path == row['File'] else 0,
                    'changed_files': row['changed_files'] if current_path == row['File'] else 0,
                    'is_file': current_path == row['File']
                })
        
        # 重複を除去（同じパスが複数回出現する可能性があるため）
        unique_paths = []
        seen_ids = set()
        for path in all_paths:
            if path['id'] not in seen_ids:
                unique_paths.append(path)
                seen_ids.add(path['id'])
        
        return pd.DataFrame(unique_paths)
    
    @staticmethod
    def generate_animated_treemap(period_dfs, path_columns, output_path, title):
        """
        時系列のTreeMapアニメーションを生成します
        """
        
        # 全期間を通じての最大変更回数を取得
        max_changes = max(
            df['changed_files'].max() for df in period_dfs.values()
        )
        
        # フレームを作成
        frames = []
        for date, period_df in period_dfs.items():
            # TreeMap用にデータを準備
            treemap_df = VideoGenerator.prepare_treemap_data(period_df)
            
            frame = go.Frame(
                data=[go.Treemap(
                    ids=treemap_df['id'],
                    parents=treemap_df['parent'],
                    values=treemap_df['Lines'],
                    branchvalues='total',
                    text=treemap_df['name'],
                    customdata=np.column_stack((
                        treemap_df['Lines'],
                        treemap_df['changed_files'],
                        treemap_df['is_file']
                    )),
                    hovertemplate='<b>Path:</b> %{id}<br>' +
                                '<b>Lines:</b> %{customdata[0]}<br>' +
                                '<b>Changes:</b> %{customdata[1]}<br>' +
                                '<extra></extra>',
                    marker=dict(
                        colors=treemap_df['changed_files'],
                        colorscale='RdBu',
                        cmid=max_changes / 2,
                        cmin=0,
                        cmax=max_changes,
                        showscale=True
                    ),
                    textinfo='label'
                )],
                name=date.strftime('%Y-%m-%d')
            )
            frames.append(frame)

        # 初期フレームのデータを使用
        initial_df = VideoGenerator.prepare_treemap_data(next(iter(period_dfs.values())))

        # 図の作成
        fig = go.Figure(
            data=[go.Treemap(
                ids=initial_df['id'],
                parents=initial_df['parent'],
                values=initial_df['Lines'],
                branchvalues='total',
                text=initial_df['name'],
                customdata=np.column_stack((
                    initial_df['Lines'],
                    initial_df['changed_files'],
                    initial_df['is_file']
                )),
                hovertemplate='<b>Path:</b> %{id}<br>' +
                            '<b>Lines:</b> %{customdata[0]}<br>' +
                            '<b>Changes:</b> %{customdata[1]}<br>' +
                            '<extra></extra>',
                marker=dict(
                    colors=initial_df['changed_files'],
                    colorscale='RdBu',
                    cmid=max_changes / 2,
                    cmin=0,
                    cmax=max_changes,
                    showscale=True
                ),
                textinfo='label'
            )],
            frames=frames,
            layout=go.Layout(
                title=dict(
                    text=f"{title}<br><sub>色は変更頻度を表します</sub>",
                    x=0.5,
                    xanchor='center'
                ),
                width=1200,
                height=800,
                updatemenus=[{
                    'type': 'buttons',
                    'showactive': False,
                    'x': 0.1,
                    'y': 1.1,
                    'buttons': [
                        {
                            'label': '再生',
                            'method': 'animate',
                            'args': [None, {
                                'frame': {'duration': 1000, 'redraw': True},
                                'fromcurrent': True,
                                'transition': {'duration': 500}
                            }]
                        },
                        {
                            'label': '一時停止',
                            'method': 'animate',
                            'args': [[None], {
                                'frame': {'duration': 0, 'redraw': False},
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }]
                        }
                    ]
                }],
                sliders=[{
                    'currentvalue': {
                        'prefix': '期間: ',
                        'xanchor': 'right'
                    },
                    'pad': {'t': 50},
                    'steps': [
                        {
                            'label': frame.name,
                            'method': 'animate',
                            'args': [[frame.name], {
                                'frame': {'duration': 1000, 'redraw': True},
                                'transition': {'duration': 500}
                            }]
                        }
                        for frame in frames
                    ]
                }]
            )
        )
        
        # HTMLファイルとして保存
        fig.write_html(output_path)
        print(f"Animated treemap has been saved to {output_path}")