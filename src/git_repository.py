import re
from collections import deque
import git
import os
import csv
from datetime import datetime
import time
from multiprocessing import Pool, cpu_count
from functools import partial


class GitRepository:
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.repo_info = self.parse_repo_url(repo_url)
        self.repo_path = self.get_repo_path()
        self.output_dir = self.generate_output_dir()
        self.repo = None
        self.repo_name = self.repo_info['repo']
        self.owner = self.repo_info['owner']
        self.clone(repo_url)

    def parse_repo_url(self, url):
        pattern = r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+)(?:\.git)?"
        match = re.search(pattern, url)
        if match:
            return {
                'owner': match.group("owner"),
                'repo': match.group("repo").rstrip('.git')
            }
        else:
            raise ValueError("Invalid GitHub URL")
        
    def get_repo_path(self):
        return os.path.join(os.getcwd(), self.repo_info['owner'], self.repo_info['repo'])

    def clone(self, remote_url):

        if not os.path.exists(self.repo_path):
            print(f"Cloning repository from {remote_url}...")
            self.repo = git.Repo.clone_from(remote_url, self.repo_path)
            print("Repository cloned successfully.")
        else:
            print("Repository already exists. Pulling latest changes...")
            self.repo = git.Repo(self.repo_path)
            self.repo.remotes.origin.pull()
            print("Repository updated successfully.")

    def get_commit_history(self, directory_path):
        if not self.repo:
            self.repo = git.Repo(self.repo_path)
        default_branch = self.repo.head.reference
        return list(self.repo.iter_commits(default_branch, paths=directory_path))
    
    def generate_output_dir(self):
        output_dir = os.path.join("out", self.repo_info['owner'], self.repo_info['repo'])
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def count_lines_in_file(self, commit_hexsha, file_path):
        if not self.repo:
            self.repo = git.Repo(self.repo_path)
        try:
            file_content = self.repo.git.show(f"{commit_hexsha}:{file_path}")
            return len(file_content.splitlines())
        except git.exc.GitCommandError:
            return 0
        
    def get_directories(self):
        if not self.repo:
            self.repo = git.Repo(self.repo_path)
    
        tree = self.repo.head.commit.tree
        directories = []
        queue = deque([(tree, '')])
    
        while queue:
            current_tree, prefix = queue.popleft()
            for item in current_tree:
                if item.type == 'tree':
                    full_path = prefix + item.path
                    directories.append(full_path)
                    queue.append((item, full_path + '/'))
    
        return directories
    
    def get_repo_name(self):
        return self.repo_name
    
    def count_lines(self, blob):
        try:
            content = blob.data_stream.read().decode('utf-8', errors='replace')
            return len(content.splitlines())
        except Exception as e:
            print(f"Error processing {blob.name}: {e}")
            return 0

    def process_commit(self, file_extensions, commit_sha):
        commit = self.repo.commit(commit_sha)
        commit_date = commit.committed_datetime
        
        # コミット情報の基本データを作成
        commit_info = {
            'Commit': commit.hexsha,
            'Date_Unix': int(commit_date.timestamp()),
            'Date_ISO': commit_date.isoformat()
        }
        
        results = []
        paths_to_process = set()  # 処理対象のパスを保持
        
        def collect_directory_paths(path):
            """パスのすべての親ディレクトリを収集"""
            parts = path.split('/')
            current_path = ''
            dirs = set()
            for part in parts[:-1]:  # 最後のパート（ファイル名）を除く
                current_path = f"{current_path}{part}/" if current_path else f"{part}/"
                dirs.add(current_path.rstrip('/'))
            return dirs

        # 初回コミットの場合
        if not commit.parents:
            for item in commit.tree.traverse():
                if item.type == 'blob':
                    if file_extensions is None or any(item.name.endswith(ext) for ext in file_extensions):
                        line_count = self.count_lines(item)
                        paths_to_process.add(item.path)
                        row = {**commit_info, 
                            'File': item.path, 
                            'Lines': line_count, 
                            'Change': 'added', 
                            'Type': 'file'}
                        results.append(row)
            
            # ディレクトリ情報の収集
            all_dirs = set()
            for path in paths_to_process:
                all_dirs.update(collect_directory_paths(path))
            
            # ディレクトリエントリの追加
            for dir_path in all_dirs:
                row = {**commit_info,
                    'File': dir_path,
                    'Lines': 0,
                    'Change': 'added',
                    'Type': 'directory'}
                results.append(row)
                
            return results
        
        # 差分の処理
        parent = commit.parents[0]
        diffs = parent.diff(commit)
        
        # 変更されたファイルを処理
        for diff in diffs:
            file_path = diff.b_path if diff.b_path else diff.a_path
            
            # 拡張子フィルタリング
            if file_extensions and not any(file_path.endswith(ext) for ext in file_extensions):
                continue
                
            paths_to_process.add(file_path)
            
            if diff.change_type == 'A':  # Added
                if diff.b_blob:
                    line_count = self.count_lines(diff.b_blob)
                    row = {**commit_info, 
                        'File': file_path, 
                        'Lines': line_count, 
                        'Change': 'added',
                        'Type': 'file'}
                    results.append(row)
                    
            elif diff.change_type == 'M':  # Modified
                if diff.b_blob:
                    line_count = self.count_lines(diff.b_blob)
                    row = {**commit_info, 
                        'File': file_path, 
                        'Lines': line_count, 
                        'Change': 'modified',
                        'Type': 'file'}
                    results.append(row)
                    
            elif diff.change_type == 'D':  # Deleted
                row = {**commit_info, 
                    'File': file_path, 
                    'Lines': 0, 
                    'Change': 'deleted',
                    'Type': 'file'}
                results.append(row)
                
            elif diff.change_type == 'R':  # Renamed
                if diff.b_blob:
                    line_count = self.count_lines(diff.b_blob)
                    row = {**commit_info, 
                        'File': diff.b_path, 
                        'Lines': line_count, 
                        'Change': 'renamed', 
                        'OldPath': diff.a_path,
                        'Type': 'file'}
                    results.append(row)
        
        # コミット時点でのディレクトリ構造を取得
        all_dirs = set()
        for path in paths_to_process:
            all_dirs.update(collect_directory_paths(path))
        
        # 現在のツリーから存在するディレクトリを確認
        for dir_path in all_dirs:
            try:
                # ディレクトリの存在確認
                commit.tree[dir_path]
                row = {**commit_info,
                    'File': dir_path,
                    'Lines': 0,
                    'Change': 'unchanged',
                    'Type': 'directory'}
                results.append(row)
            except KeyError:
                # このディレクトリは削除された可能性がある
                pass
        
        return results

    def process_commits(self, csv_filename, file_extensions=None, batch_size=100, start_commit=None):
        # フィールド名の定義を一箇所に集中化
        self.fieldnames = ['Commit', 'Date_Unix', 'Date_ISO', 'File', 'Lines', 'Change', 'OldPath', 'Type']

        # 既存のファイルを削除
        if os.path.exists(csv_filename):
            os.remove(csv_filename)
            print(f"Removed existing CSV file: {csv_filename}")

        # ヘッダーの書き込み
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()

        commits = list(self.repo.iter_commits(self.repo.active_branch.name))
        total_commits = len(commits)

        if start_commit:
            start_index = next((i for i, c in enumerate(commits) if c.hexsha == start_commit), 0)
            commits = commits[start_index:]

        start_time = time.time()
        processed_commits = 0

        num_processes = cpu_count()
        pool = Pool(processes=num_processes)
        process_commit_partial = partial(self.process_commit, file_extensions)

        for i in range(0, len(commits), batch_size):
            batch_commits = commits[i:i+batch_size]
            results = pool.map(process_commit_partial, [commit.hexsha for commit in batch_commits])
            
            flattened_results = [item for sublist in results for item in sublist]
            
            self.write_results(csv_filename, flattened_results)
            
            processed_commits += len(batch_commits)
            elapsed_time = time.time() - start_time
            commits_per_second = processed_commits / elapsed_time
            estimated_time = (total_commits - processed_commits) / commits_per_second
            
            print(f"Processed {processed_commits}/{total_commits} commits. "
                f"Estimated time remaining: {estimated_time:.2f} seconds")

        pool.close()
        pool.join()

        print(f"Total commits processed: {processed_commits}")

    def write_results(self, csv_filename, results):
        # クラスのフィールド名を使用
        with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            for row in results:
                # 必要なフィールドがない場合のデフォルト値を設定
                row_with_defaults = {
                    'Commit': row.get('Commit', ''),
                    'Date_Unix': row.get('Date_Unix', 0),
                    'Date_ISO': row.get('Date_ISO', ''),
                    'File': row.get('File', ''),
                    'Lines': row.get('Lines', 0),
                    'Change': row.get('Change', 'unchanged'),
                    'OldPath': row.get('OldPath', ''),
                    'Type': row.get('Type', 'file')
                }
                writer.writerow(row_with_defaults)