import os
import pandas as pd
import webbrowser
from .git_repository import GitRepository
from .commit_analyzer import CommitAnalyzer
from .dataframe_creator import DataFrameCreator
from .video_generator import VideoGenerator


class RepositoryTimelapse:
    def __init__(self, repo_url, aggregation_period="D"):
        self.repo = GitRepository(repo_url)
        self.analyzer = CommitAnalyzer()
        self.df_creator = DataFrameCreator()
        self.video_generator = VideoGenerator()
        self.aggregation_period = aggregation_period

    def clone_repository(self, repo_url):
        self.repo.clone(repo_url)

    def process_directory(self, directory):
        commits = self.repo.get_commit_history(directory)
        commit_data = self.analyzer.analyze_commits(self.repo, commits, directory)
        df = self.df_creator.create_dataframe(self.repo, directory, commit_data)
        # df = self.df_creator.process_dataframe(df)
        
        # 新しい集計ステップ
        df = self.df_creator.aggregate_dataframe(df, self.aggregation_period)
        
        base_name = os.path.basename(directory).replace('/', '_')
        period_name = 'daily' if self.aggregation_period == 'D' else 'weekly'
        output_path = os.path.join(self.output_dir, f"line_count_race_{period_name}_{base_name}.mp4")

        
        # self.video_generator.generate_video(df, output_path, f'{directory} ディレクトリのコード行数推移 ({period_name})')
        self.video_generator.generate_plotly_animation(df, 'out/binarycompatibility.html', f'{directory} ディレクトリのコード行数推移 ({period_name})')
        print(f"{directory} の{period_name}動画が {output_path} に生成されました。")

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

    def run_extended_analysis(self, repo_url, file_extensions=None):
        # self.clone_repository(repo_url)
        csv_filename = self.generate_commit_history_csv(file_extensions)
        self.generate_treemap(csv_filename)
        # 元の分析を実行する場合はここでコメントを外してください
        # self.process_directory(directory)
    
    def run(self, repo_url):
        # self.clone_repository(repo_url)
        directories = self.repo.get_directories()
        for directory in directories:
            print(f"Processing {directory}...")
            self.create_csv(directory)
            # self.process_directory(directory)