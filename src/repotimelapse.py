import os
import pandas as pd
import webbrowser
import csv
from .git_repository import GitRepository
from .dataframe_creator import DataFrameCreator
from .video_generator import VideoGenerator


class RepositoryTimelapse:
    def __init__(self, repo_url):
        self.repo = GitRepository(repo_url)
        self.df_creator = DataFrameCreator()
        self.video_generator = VideoGenerator()

    def run(self):
        self.generate_treemap()
        self.generate_bar_chart()

    def generate_treemap(self):
        repo_structure = self.repo.get_repo_structure(sample_interval='YE')
        treemap_df = DataFrameCreator.create_dataframe(repo_structure)
        treemap_df.to_csv(os.path.join(self.generate_output_dir(), "treemap_data.csv"), index=False)
        self.video_generator.generate_extend_treemap(treemap_df, os.path.join(self.generate_output_dir(), 'treemap.html'))

    def generate_output_dir(self):
        output_dir = os.path.join("out", self.repo.owner, self.repo.repo_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def generate_csv_filename(self, commit):
        # コミットのタイムスタンプを使用して一意のファイル名を生成
        timestamp = commit.committed_datetime.strftime("%Y%m%d_%H%M%S")
        return f"repo_structure_{timestamp}.csv"
    
    def generate_bar_chart(self):
        repo_structure = self.repo.get_current_stucture()
        df = DataFrameCreator.create_dataframe(repo_structure)
        df.to_csv(os.path.join(self.generate_output_dir(), "current_structure.csv"), index=False)