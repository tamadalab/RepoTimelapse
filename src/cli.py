import argparse

class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Analyze and visualize repository timeline.')
        self._add_arguments()

    def _add_arguments(self):
        self.parser.add_argument('--repo_url', type=str, default="https://github.com/stleary/JSON-java.git", help='URL of the repository to analyze')
        self.parser.add_argument('--extensions', nargs='+', default=['.gradle', '.java', '.kt', '.xml'], 
                                 help='File extensions to analyze (e.g., .java .kt .xml)')
        self.parser.add_argument('--output', type=str, default='out', help='Output directory for results')


    def parse_args(self):
        args = self.parser.parse_args()
        if not args.repo_url:
            args.repo_url = input("Enter the URL of the repository you want to analyze: ")
        return args