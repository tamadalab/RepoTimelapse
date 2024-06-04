#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '0.1.0'
__date__ = '2024/05/31 (created: 2024/05/31)'

import pandas as pd
from collections import defaultdict

class CommitDataProcessor:
    def __init__(self, commits):
        self.commits = commits
        self.commit_timestampes = []
        self.file_changes = defaultdict(list)
        self.file_line_counts = defaultdict(lambda: 0)

    def run(self):
        self.commits.reverse()
        self.process_commits()
        df = self.to_dataframe()
        return df

    def process_commits(self):
        for commit in self.commits:
            self.process_commit(commit)
        self.equalize_list_lengths()
        
    def process_commit(self, commit):
        node = commit["node"]
        commit_date = node["committedDate"]
        self.commit_timestamps.append(commit_date)
        files = self.extract_files_from_commit(node)
        self.update_file_line_counts(files)
        self.append_line_counts_to_dict()
        self.maintain_line_counts_for_unmodified_files()

    def extract_files_from_commit(self, node):
        if node["associatedPullRequests"]["edges"]:
            return node["associatedPullRequests"]["edges"][0]["node"]["files"]["edges"]
        return []

    def update_file_line_counts(self, files):
        for file in files:
            if file["node"]["path"].endwith(".java"):
                file_path = file["node"]["path"]
                additions = file["node"]["additions"]
                deletions = file["node"]["deletions"]
                self.file_line_counts[file_path] += additions - deletions

    def append_line_counts_to_dict(self):
        for file_path in self.file_line_counts.keys():
            self.file_changes[file_path].append(self.file_line_counts[file_path])

    def equalize_list_lengths(self):
        for file_path in self.file_changes.keys():
            while len(self.file_changes[file_path]) < len(self.commit_timestamps):
                self.file_changes[file_path].append(self.file_changes[file_path][-1])

    def to_dataframe(self):
        df = pd.DataFrame(self.file_changes, index=pd.to_datetime(self.commit_timestamps))
        df = df.fillna(method="ffill")
        return df