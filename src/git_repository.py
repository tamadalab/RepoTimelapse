import re
import git
import os
import csv
import time
from datetime import datetime, timezone
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class GitRepository:
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.repo_info = self.parse_repo_url(repo_url)
        self.repo_path = self.get_repo_path()
        self.repo = None
        self.default_branch = None
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

        origin = self.repo.remotes.origin
        self.default_branch = origin.refs['HEAD'].reference.remote_head

    def process_commit(self, commit):
            commit_date = time.strftime("%a, %d %b %Y %H:%M", time.gmtime(commit.committed_date))
            return self.traverse_tree(commit.tree, commit_date, commit)

    def write_results(self, csv_filename, results):
        fieldnames = ['Commit', 'Date_Unix', 'Date_ISO', 'File', 'Lines']
        mode = 'a' if os.path.exists(csv_filename) else 'w'
        with open(csv_filename, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if mode == 'w':
                writer.writeheader()
            for row in results:
                writer.writerow(row)

    def get_repo_structure(self, sample_interval='1M', end_date=None, max_workers=1):
        sampled_commits = self.get_sampled_commits(sample_interval, end_date)
        all_data = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_commit = {executor.submit(self.process_commit, commit): commit for commit in sampled_commits}
        
            for future in tqdm(as_completed(future_to_commit), total=len(sampled_commits), desc="Processing commits"):
                try:
                    commit_data = future.result()
                    all_data.extend(commit_data)
                except Exception as e:
                    print(f"Error processing commit: {str(e)}")

        return all_data
    
    def get_current_stucture(self):
        commit = self.repo.head.commit
        return self.traverse_tree(commit.tree, commit.committed_date, commit)
        
        
    def get_sampled_commits(self, interval='M', end_date=None):
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        else:
            end_date = pd.to_datetime(end_date).tz_localize(timezone.utc)

        # 全コミットを取得
        all_commits = list(self.repo.iter_commits('master'))
        
        # コミットをDataFrameに変換
        commit_df = pd.DataFrame({
            'commit': all_commits,
            'date': [pd.to_datetime(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(c.committed_date)), utc=True) for c in all_commits]
        })
        
        # 日付でソートし、指定された間隔でリサンプリング
        commit_df = commit_df.sort_values('date').set_index('date')
        sampled = commit_df.resample(interval).first()
        
        # end_dateより新しいコミットを除外
        sampled = sampled[sampled.index <= end_date]
        
        return sampled['commit'].dropna().tolist()
    
    def traverse_tree(self, tree, commit_date, commit_hash, path=''):
        items = []
        for item in tree.traverse():
            if item.type == 'blob':  # File
                size = self.count_lines(item)
                items.append({
                    'path': item.path,
                    'name': item.name,
                    'type': 'file',
                    'size': size,
                    'extension': os.path.splitext(item.path)[1],
                    'date': commit_date,
                    'commit_hash': commit_hash,
                    'parent': item.path.split('/')[-2] if '/' in item.path else 'root'
                })
            # elif item.type == 'tree':  # Directory
            #     items.append({
            #         'path': item.path,
            #         'name': item.name,
            #         'type': 'directory',
            #         'size': 0,
            #         'extension': '',
            #         'date': commit_date,
            #         'commit_hash': commit_hash,
            #         'parent': item.path.split('/')[-2] if '/' in item.path else 'root'
            #     })
                # items.extend(self.traverse_tree(item, commit_date, commit_hash, path=item.path))
        return items
    
    def count_lines(self, blob):
        try:
            return len(blob.data_stream.read().decode('utf-8').splitlines())
        except UnicodeDecodeError:
            # バイナリファイルの場合は0行として扱う
            return 0
        
    def all_commit_data(self):
        all_commits = list(self.repo.iter_commits(self.default_branch))
        items = []
        for commit in reversed(all_commits):
            stats = commit.stats
            files = len(commit.tree.blobs)
            items.append(
                {
                    'commit_hexsha': commit.hexsha,
                    'date': commit.committed_datetime.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None),
                    'insertions': stats.total['insertions'],
                    'deletions': stats.total['deletions'],
                    'files': files
                }
            )
        return items
