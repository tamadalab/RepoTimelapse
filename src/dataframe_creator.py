import pandas as pd
import os
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

class DataFrameCreator:
    @staticmethod
    def create_dataframe(repo, directory_path, commit_data, max_workers=4):
        data = {}
        current_files = {}

        def process_commit(commit):
            try:
                commit_date = commit["date"].strftime('%Y-%m-%d %H:%M:%S')
                commit_hexsha = commit["commit_hexsha"]
                
                changed_files = {file["file_path"] for file in commit["files"] if file["file_path"].startswith(directory_path)}
                files_to_update = set(current_files.keys()) | changed_files
                
                updated_files = {}
                commit_tree = repo.commit(commit_hexsha).tree
                for file_path in files_to_update:
                    try:
                        file_blob = commit_tree[file_path[len(directory_path):]]
                        line_count = file_blob.data_stream.read().decode('utf-8').count('\n')
                        if line_count > 0:
                            updated_files[file_path] = line_count
                    except KeyError:
                        pass

                return commit_date, updated_files
            except Exception as e:
                print(f"Error processing commit {commit_hexsha}: {str(e)}")
                return None, None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_commit = {executor.submit(process_commit, commit): commit for commit in reversed(commit_data)}
            
            for future in tqdm(as_completed(future_to_commit), total=len(commit_data), desc="Processing commits"):
                commit_date, updated_files = future.result()
                if commit_date and updated_files:
                    current_files.update(updated_files)
                    data[commit_date] = current_files.copy()
 
        return pd.DataFrame(data).T.fillna(0)
    
    @staticmethod
    def process_dataframe(df):
        df.columns = [os.path.basename(col) for col in df.columns]
        return df
    
    @staticmethod
    def aggregate_dataframe(df, period='W'):
        """
        データフレームを指定した期間で集計します。
        
        :param df: 元のデータフレーム
        :param period: 集計期間 ('D' for daily, 'W' for weekly)
        :return: 集計されたデータフレーム
        """
        df.index = pd.to_datetime(df.index)
        
        if period == 'D':
            return df.resample('D').last().ffill()
        elif period == 'W':
            return df.resample('W').last().ffill()
        elif period == 'M':
            return df.resample('M').last().ffill()
        elif period == 'Y':
            return df.resample('Y').last().ffill()
        else:
            raise ValueError("Invalid period. Use 'D' for daily or 'W' for weekly.")
    
    @staticmethod
    def create_dataframe(repo_structure, owner):
        df = pd.DataFrame(repo_structure)
        return df
    
    @staticmethod
    def extension_dataframe(repo_structure):
        df = pd.DataFrame(repo_structure)
        new_df = df.groupby('extension')['size'].sum().reset_index()
        new_df = new_df[new_df['extension'].str.strip() != '']
        new_df = new_df.sort_values('size', ascending=False)
        return new_df
    
    @staticmethod
    def file_count_dataframe(repo_structure):
        df = pd.DataFrame(repo_structure)
        df['date'] = pd.to_datetime(df['date'])
        df_sorted = df.sort_values('date')
        df_sorted = df_sorted.reset_index(drop=True)
        return df_sorted
    
    @staticmethod
    def total_line_count_dataframe(repo_structure):
        df = pd.DataFrame(repo_structure)
        df['date'] = pd.to_datetime(df['date'])
        df_sorted = df.sort_values('date')
        df_sorted = df_sorted.reset_index(drop=True)
        df_sorted['total_lines'] = (df_sorted['insertions'] - df_sorted['deletions']).cumsum()
        return df_sorted
    