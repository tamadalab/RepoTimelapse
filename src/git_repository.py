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
        commit_info = {
            'Commit': commit.hexsha,
            'Date_Unix': int(commit_date.timestamp()),
            'Date_ISO': commit_date.isoformat()
        }
        
        results = []
        for item in commit.tree.traverse():
            if item.type == 'blob':
                if file_extensions is None or any(item.name.endswith(ext) for ext in file_extensions):
                    line_count = self.count_lines(item)
                    row = {**commit_info, 'File': item.path, 'Lines': line_count}
                    results.append(row)
        return results

    def process_commits(self, csv_filename, file_extensions=None, batch_size=100, start_commit=None):
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
        fieldnames = ['Commit', 'Date_Unix', 'Date_ISO', 'File', 'Lines']
        mode = 'a' if os.path.exists(csv_filename) else 'w'
        with open(csv_filename, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if mode == 'w':
                writer.writeheader()
            for row in results:
                writer.writerow(row)

    def get_repo_structure(self, commit):
        structure = []
        for item in commit.tree.traverse():
            if item.type == 'blob':  # ファイル
                structure.append({
                    'path': item.path.split('/'),
                    'size': item.size,
                    'parent': '/'.join(item.path.split('/')[:-1]),
                    'name': item.name,
                    'file_change_count': self.get_file_change_count(item.path, commit.committed_date),
                })
        print(len(structure))
        return structure
    
    def get_file_change_count(repo, file_path, until_date):
        """指定された日付までのファイルの変更回数を取得"""
        try:
            return int(repo.git.rev_list('--count', 'HEAD', '--', file_path, before=until_date))
        except:
            return 0
        
    def get_sampled_commits(self, num_samples=20):
        all_commits = list(self.repo.iter_commits())
        first_commit_time = all_commits[-1].committed_datetime
        last_commit_time = all_commits[0].committed_datetime
        time_range = last_commit_time - first_commit_time
        interval = time_range / (num_samples - 1)

        sampled_commits = []
        for i in range(num_samples):
            target_time = first_commit_time + i * interval
            closest_commit = min(all_commits, key=lambda x: abs(x.committed_datetime - target_time))
            sampled_commits.append(closest_commit)
        return sampled_commits