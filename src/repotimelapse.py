import os
from .git_repository import GitRepository
from .commit_analyzer import CommitAnalyzer
from .dataframe_creator import DataFrameCreator
from .video_generator import VideoGenerator


class RepositoryTimelapse:
    def __init__(self, repo_url, output_dir="out", aggregation_period="D"):
        self.repo = GitRepository(repo_url)
        self.analyzer = CommitAnalyzer()
        self.df_creator = DataFrameCreator()
        self.video_generator = VideoGenerator()
        self.output_dir = output_dir
        self.aggregation_period = aggregation_period
        os.makedirs(self.output_dir, exist_ok=True)

    def clone_repository(self, repo_url, branch="master"):
        self.repo.clone(repo_url, branch)

    def process_directory(self, directory):
        commits = self.repo.get_commit_history(directory)
        commit_data = self.analyzer.analyze_commits(self.repo, commits, directory)
        df = self.df_creator.create_dataframe(self.repo, directory, commit_data)
        df = self.df_creator.process_dataframe(df)
        
        # 新しい集計ステップ
        df = self.df_creator.aggregate_dataframe(df, self.aggregation_period)
        
        base_name = os.path.basename(directory).replace('/', '_')
        period_name = 'daily' if self.aggregation_period == 'D' else 'weekly'
        output_path = os.path.join(self.output_dir, f"line_count_race_{period_name}_{base_name}.mp4")

        
        # self.video_generator.generate_video(df, output_path, f'{directory} ディレクトリのコード行数推移 ({period_name})')
        self.video_generator.generate_plotly_animation(df, 'out/binarycompatibility.html', f'{directory} ディレクトリのコード行数推移 ({period_name})')
        print(f"{directory} の{period_name}動画が {output_path} に生成されました。")

    def run(self, repo_url, directories, branch="master"):
        self.clone_repository(repo_url, branch)
        for directory in directories:
            print(f"Processing {directory}...")
            self.process_directory(directory)
