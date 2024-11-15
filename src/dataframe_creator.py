import pandas as pd
import os
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
    def treemap_dateframe(csv_filename):
        df = pd.read_csv(csv_filename)
        
        # データの前処理
        df['date'] = pd.to_datetime(df['Date_ISO'], utc=True)
        df_latest = df.sort_values('date').groupby('File').last().reset_index()
        file_counts = df['File'].value_counts()
        df_latest['changed_files'] = df_latest['File'].map(file_counts)
        
        # ファイルパスの処理
        path_parts = df_latest['File'].str.split('/', expand=True)
        for i in range(len(path_parts.columns)):
            df_latest[f'path_{i}'] = path_parts[i]
             
        df_latest['size'] = df_latest['Lines']
        
        # 動的にパスカラムのリストを作成
        path_columns = [f'path_{i}' for i in range(len(path_parts.columns))]

        return df_latest, path_columns
    
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
    def create_time_series_df(df, period='Y'):
         # dateでソート
        df = df.sort_values('date')
        
        # 期間の開始時点を取得
        period_starts = pd.date_range(
            start=df['date'].min(),
            end=df['date'].max(),
            freq=period
        )
        
        # 各期間の累積DataFrameを作成
        cumulative_dfs = {}
        
        for period_end in period_starts:
            # その期間までの全データを取得
            period_mask = df['date'] <= period_end
            period_df = df[period_mask].copy()
            
            if not period_df.empty:
                # 各ファイルの最新状態を取得
                latest_state = period_df.groupby('File').last().reset_index()
                
                # Lines > 0 のファイルのみを保持（削除されたファイルを除外）
                latest_state = latest_state[latest_state['Lines'] > 0]
                
                if not latest_state.empty:
                    # changed_files を再計算
                    # その期間までの各ファイルの変更回数
                    file_changes = period_df['File'].value_counts()
                    latest_state['changed_files'] = latest_state['File'].map(file_changes)
                    
                    cumulative_dfs[period_end] = latest_state
        
        return cumulative_dfs
    
    @staticmethod
    def create_cumulative_time_series_df(df, period='Y'):
        """
        時系列データを指定した期間で区切り、累積的なDataFrameを作成します
        
        :param df: 元のDataFrame (date, File, Lines, changed_filesカラムを含む)
        :param period: 期間('Y', 'M', 'W', 'D'のいずれか)
        :return: 期間ごとの累積DataFrameのディクショナリ
        """
        print(f"Processing data from {df['date'].min()} to {df['date'].max()}")
        
        # dateでソート
        df = df.sort_values('date')
        
        # 期間の開始時点を取得
        period_starts = pd.date_range(
            start=df['date'].min(),
            end=df['date'].max(),
            freq=period
        )
        print(f"Found {len(period_starts)} periods")
        
        # 各期間の累積DataFrameを作成
        cumulative_dfs = {}
        
        for period_end in period_starts:
            # その期間までの全データを取得
            period_mask = df['date'] <= period_end
            period_df = df[period_mask].copy()
            
            if not period_df.empty:
                # 各ファイルの最新状態を取得
                latest_state = period_df.groupby('File').last().reset_index()
                latest_state = latest_state[latest_state['Lines'] > 0]
                
                if not latest_state.empty:
                    # changed_files を再計算
                    file_changes = period_df['File'].value_counts()
                    latest_state['changed_files'] = latest_state['File'].map(file_changes)
                    
                    # ファイルパスを分解してpath_partsカラムを追加
                    latest_state['path_parts'] = latest_state['File'].apply(lambda x: x.split('/'))

                    print(f"Period {period_end}: {len(latest_state)} files")
                    cumulative_dfs[period_end] = latest_state

                    print(latest_state)
        return cumulative_dfs