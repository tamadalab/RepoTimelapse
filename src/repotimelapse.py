import os
import pandas as pd
import webbrowser
from .git_repository import GitRepository
from .commit_analyzer import CommitAnalyzer
from .dataframe_creator import DataFrameCreator
from .video_generator import VideoGenerator


class RepositoryTimelapse:
    def __init__(self, repo_url):
        self.repo = GitRepository(repo_url)
        self.analyzer = CommitAnalyzer()
        self.df_creator = DataFrameCreator()
        self.video_generator = VideoGenerator()

    def generate_commit_history_csv(self, file_extensions=None, batch_size=100, start_commit=None):
        csv_filename = os.path.join(self.repo.output_dir, "commit_history.csv")
        self.repo.process_commits(csv_filename, file_extensions, batch_size, start_commit)
        print(f"Commit history CSV has been generated: {csv_filename}")
        return csv_filename

    def generate_treemap(self, csv_filename):
        df_latest, path_columns = self.df_creator.treemap_dateframe(csv_filename)
        output_path = os.path.join(self.repo.output_dir, "file_structure_treemap.html")
        self.video_generator.generate_treemap(df_latest, output_path, 'File Structure Treemap', path_columns)
        print(f"Treemap has been generated: {output_path}")
        webbrowser.open('file://' + os.path.realpath(output_path))

    def run_extended_analysis(self, file_extensions=None):
        csv_filename = self.generate_commit_history_csv(file_extensions)
        self.generate_treemap(csv_filename)