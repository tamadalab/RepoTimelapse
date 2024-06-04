#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '0.1.0'
__date__ = '2024/06/04 (created: 2024/05/31)'

from abc import ABC, abstractmethod

class OutputStrategy(ABC):

    @abstractmethod
    def output(self, df, filename):
        pass