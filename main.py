#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '1.0.0'
__date__ = '2024/09/10 (created: 2024/05/31)'

from src.cli import CLI
from src.repotimelapse import RepositoryTimelapse

def main():
    cli = CLI()
    args = cli.parse_args()

    processor = RepositoryTimelapse(args.repo_url)
    processor.run_extended_analysis()

if __name__ == "__main__":
    main()