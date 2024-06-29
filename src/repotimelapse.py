import os
from .git_repository import GitRepository
from .commit_analyzer import CommitAnalyzer
from .dataframe_creator import DataFrameCreator
from .video_generator import VideoGenerator

class RepositoryTimelapse:
    def __init__(self, repo_path):
        self.repo = GitRepository(repo_path)
        self.analyzer = CommitAnalyzer()
        self.df_creator = DataFrameCreator()
        self.video_generator = VideoGenerator()

    def clone_repository(self, remote_url, branch='master'):
        self.repo.clone(remote_url, branch)

    def process_directory(self, directory):
        commits = self.repo.get_commit_history(directory)
        commit_data = self.analyzer.analyze_commits(self.repo, commits, directory)
        df = self.df_creator.create_dataframe(self.repo, directory, commit_data)
        df = self.df_creator.process_dataframe(df)
        
        output_path = f"line_count_race_{os.path.basename(directory)}.mp4"
        self.video_generator.generate_video(df, output_path, f'{directory} ディレクトリのコード行数推移')
        print(f"{directory} の動画が {output_path} に生成されました。")

    def run(self, remote_url, directories, branch='master'):
        self.clone_repository(remote_url, branch)
        for directory in directories:
            print(f"Processing {directory}...")
            self.process_directory(directory)