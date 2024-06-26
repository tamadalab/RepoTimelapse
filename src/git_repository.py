import git
import os

class GitRepository:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = None

    def clone(self, remote_url, branch='master'):
        if not os.path.exists(self.repo_path):
            print(f"Cloning repository from {remote_url}...")
            self.repo = git.Repo.clone_from(remote_url, self.repo_path, branch=branch)
            print("Repository cloned successfully.")
        else:
            print("Repository already exists. Pulling latest changes...")
            self.repo = git.Repo(self.repo_path)
            self.repo.remotes.origin.pull()
            print("Repository updated successfully.")

    def get_commit_history(self, directory_path):
        if not self.repo:
            self.repo = git.Repo(self.repo_path)
        main_branch = self.repo.heads.master
        return list(self.repo.iter_commits(main_branch, paths=directory_path))

    def count_lines_in_file(self, commit_hexsha, file_path):
        if not self.repo:
            self.repo = git.Repo(self.repo_path)
        try:
            file_content = self.repo.git.show(f"{commit_hexsha}:{file_path}")
            return len(file_content.splitlines())
        except git.exc.GitCommandError:
            return 0