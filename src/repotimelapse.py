import os
import pandas as pd
from .git_repository import GitRepository
from .dataframe_creator import DataFrameCreator
from .video_generator import VideoGenerator


class RepositoryTimelapse:
    def __init__(self, repo_url):
        self.repo = GitRepository(repo_url)
        self.df_creator = DataFrameCreator()
        self.video_generator = VideoGenerator()

    def run(self):
        # self.generate_treemap()
        self.generate_bar_chart()
        # self.generate_pie_chart()
        # self.total_line_count()
        # self.file_count()

    def generate_treemap(self):
        repo_structure = self.repo.get_repo_structure(sample_interval='YE')
        treemap_df = self.df_creator.create_dataframe(repo_structure, self.repo.repo_name)
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
        df = DataFrameCreator.extension_dataframe(repo_structure)
        df.to_csv(os.path.join(self.generate_output_dir(), "extension.csv"), index=False)
        output_path = os.path.join(self.generate_output_dir(), 'extension_bar.html')
        self.video_generator.bar_chart(df, output_path)

    def generate_pie_chart(self):
        repo_structure = self.repo.get_current_stucture()
        df = DataFrameCreator.extension_dataframe(repo_structure)
        df.to_csv(os.path.join(self.generate_output_dir(), "extension.csv"), index=False)
        output_path = os.path.join(self.generate_output_dir(), 'extension_pie.html')
        self.video_generator.pie_chart(df, output_path)

    def total_line_count(self):
        repo_structure = self.repo.all_commit_data()
        df = DataFrameCreator.total_line_count_dataframe(repo_structure)
        df.to_csv(os.path.join(self.generate_output_dir(), "total_line_count.csv"), index=False)
        output_path = os.path.join(self.generate_output_dir(), 'total_line_count.html')
        self.video_generator.total_line_count(df, output_path)

    def file_count(self):
        repo_structure = self.repo.all_commit_data()
        df = DataFrameCreator.file_count_dataframe(repo_structure)
        df.to_csv(os.path.join(self.generate_output_dir(), "file_count.csv"), index=False)
        output_path = os.path.join(self.generate_output_dir(), 'file_count.html')
        self.video_generator.file_count(df, output_path)