#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '0.1.0'
__date__ = '2024/05/31 (created: 2024/05/31)'

from src.repotimelapse import RepositoryTimelapse

def main():
    repo_url = "https://github.com/tamadalab/MarryLab"
    # repo_url = "https://github.com/SonarSource/sonarqube.git"
    file_extensions = ['.gradle', '.java', '.kt', '.xml']  # 分析対象のファイル拡張子

    processor = RepositoryTimelapse(repo_url)
    processor.run_extended_analysis(repo_url, file_extensions)

if __name__ == "__main__":
    main()