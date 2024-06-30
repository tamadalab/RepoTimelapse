#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '0.1.0'
__date__ = '2024/05/31 (created: 2024/05/31)'

from src.repotimelapse import RepositoryTimelapse

if __name__ == "__main__":
    repo_path = "gradle"
    remote_url = "https://github.com/gradle/gradle.git"
    directories = [
        'build-logic/binary-compatibility/src/main/groovy/gradlebuild/binarycompatibility',
    ]
    
    processor = RepositoryTimelapse(repo_path)
    processor.run(remote_url, directories) 