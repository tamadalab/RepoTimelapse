import pandas as pd
import plotly.express as px


class TreeMapGenerator:
    @staticmethod
    def generate_treemap(df, output_path, path_columns, title="Example Treemap"):
        fig = px.treemap(
            df,
            path=path_columns,  # 動的に作成したパスカラムのリストを使用
            values="size",
            color="date",
            hover_data=["date", "lines"],
            title=title
        )
        fig.write_html(output_path)
        fig.show()
