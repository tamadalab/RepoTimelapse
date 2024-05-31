#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""RepoTimelapse：GitHubのリポジトリURLからリポジトリの成長過程を動画化する。"""
__author__ = 'Hayami Kento'
__version__ = '0.1.0'
__date__ = '2024/05/31 (created: 2024/05/31)'

import os
import dotenv
import re
import requests

class Repository:
    def __init__(self):
        dotenv.load_dotenv()
        self.url = os.getenv('REPO_URL')
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_name = None
        self.owner = None
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.api_url = "https://api.github.com/graphql"

    def parse_url(self, cursor=None):
        pattern = r'github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+)(?:\.git)?'
        match = re.search(pattern, self.url)
    
        if match:
            self.owner = match.group('owner')
            self.repo_name = match.group('repo')
        else:
            raise ValueError("Invalid GitHub URL")

    def fetch_commits(self, cursor=None):
        query = """
    query ($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        ref(qualifiedName: "main") {
          target {
            ... on Commit {
              history(first: 100, after: $cursor) {
                edges {
                  node {
                    oid
                    committedDate
                    additions
                    deletions
                    changedFilesIfAvailable
                    associatedPullRequests(first: 1) {
                      edges {
                        node {
                          files(first: 100) {
                            edges {
                              node {
                                path
                                additions
                                deletions
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
          }
        }
      }
    }
    """
        variables = {
            "owner": self.owner,
            "repo": self.repo_name,
            "cursor": cursor
        }
        response = requests.post(self.api_url, json={'query': query, 'variables': variables}, headers=self.headers)
        print(f"Status Code: {response.status_code}")
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON")
            raise

    def get_all_commits(self):
        cursor = None
        has_next_page = True
        all_commits = []

        while has_next_page:
            result = self.fetch_commits(cursor)
            commits = result['data']['repository']['ref']['target']['history']['edges']
            all_commits.extend(commits)
            page_info = result['data']['repository']['ref']['target']['history']['pageInfo']
            cursor = page_info['endCursor']
            has_next_page = page_info['hasNextPage']
        return all_commits

if __name__ == '__main__':
    aRepository = Repository()
    aRepository.parse_url()
    print(len(aRepository.get_all_commits()))