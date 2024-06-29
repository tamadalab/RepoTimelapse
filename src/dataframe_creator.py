import pandas as pd
import os

class DataFrameCreator:
    @staticmethod
    def create_dataframe(repo, directory_path, commit_data):
        data = {}
        current_files = {}

        for commit in reversed(commit_data):
            commit_date = commit["date"].strftime('%Y-%m-%d-%H-%M-%S')
            commit_hexsha = commit["commit_hexsha"]
            
            for file_path in list(current_files.keys()):
                current_files[file_path] = repo.count_lines_in_file(commit_hexsha, file_path)

            for file in commit["files"]:
                file_path = file["file_path"]
                if file_path.startswith(directory_path):
                    current_files[file_path] = repo.count_lines_in_file(commit_hexsha, file_path)

            current_files = {k: v for k, v in current_files.items() if v > 0}
            data[commit_date] = current_files.copy()

        return pd.DataFrame(data).T.fillna(0)

    @staticmethod
    def process_dataframe(df):
        df.columns = [os.path.basename(col) for col in df.columns]
        return df