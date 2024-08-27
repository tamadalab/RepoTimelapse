import git

class CommitAnalyzer:
    @staticmethod
    def analyze_commits(repo, commits, directory_path):
        commit_data = []
        for commit in commits:
            commit_info = {
                "commit_hexsha": commit.hexsha,
                "author": commit.author.name,
                "date": commit.committed_datetime,
                "message": commit.message,
                "files": CommitAnalyzer.extract_file_info(commit, directory_path)
            }
            commit_data.append(commit_info)
        return commit_data

    @staticmethod
    def extract_file_info(commit, directory_path):
        file_stats = commit.stats.files
        files = []
        for file_path, stats in file_stats.items():
            if file_path.startswith(directory_path):
                file_info = {
                    "file_path": file_path,
                    "insertions": stats['insertions'],
                    "deletions": stats['deletions']
                }
                files.append(file_info)
        return files
    
