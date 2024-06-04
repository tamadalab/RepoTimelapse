#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '0.1.0'
__date__ = '2024/06/04 (created: 2024/05/31)'

import pandas as pd
import bar_chart_race as bcr

from output_strategy import OutputStrategy

class VideoOutput(OutputStrategy):
    def output(self, df):
        bcr.bar_chart_race(df=df,
                           filename="file_line_count_changes.mp4",
                           title="Changes in Lines of Code per File over Time",
        )