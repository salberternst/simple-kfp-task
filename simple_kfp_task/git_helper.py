import os
import sys
from git import Repo

class GitHelper:
    """
    A helper class for interacting with Git repositories.
    """

    def __init__(self):
        """
        Initializes a new instance of the GitHelper class.
        """
        try:
            self.repo = Repo('.', search_parent_directories=True)
        except:
            print(f"{os.getcwd()} is not a Git repository.")
            sys.exit(1)

    def get_remote_url(self, remote='origin'):
        """
        Retrieves the URL of the specified remote.

        Args:
            remote (str, optional): The name of the remote. Defaults to 'origin'.

        Returns:
            str: The URL of the remote, or None if the remote does not exist.
        """
        try:
            git_origin = self.repo.remotes[remote].url
            return git_origin
        except:
            return None

    def is_git_dirty(self):
        """
        Checks if the Git repository has any uncommitted changes.

        Returns:
            bool: True if the repository is dirty, False otherwise.
        """
        try:
            return self.repo.is_dirty()
        except:
            return False

    def get_current_branch(self):
        """
        Retrieves the name of the current branch.

        Returns:
            str: The name of the current branch, or None if the branch cannot be determined.
        """
        try:
            return self.repo.active_branch.name
        except:
            return None

    def get_current_commit(self):
        """
        Retrieves the SHA hash of the current commit.

        Returns:
            str: The SHA hash of the current commit, or None if the commit cannot be determined.
        """
        try:
            return self.repo.head.commit.hexsha
        except:
            return None

    def get_last_commit_on_remote(self, remote='origin'):
        """
        Retrieves the SHA hash of the last commit on the remote branch.

        Args:
            remote (str, optional): The name of the remote. Defaults to 'origin'.

        Returns:
            str: The SHA hash of the last commit on the remote branch, or None if the commit cannot be determined.
        """
        try:
            remote_branch = self.repo.remotes[remote].refs[self.repo.active_branch.name]
            last_commit = remote_branch.commit.hexsha
            return last_commit
        except:
            return None

    def build_git_diff(self, commit=None):
        """
        Builds the diff between the specified commit and the current branch.

        Args:
            commit (str, optional): The SHA hash of the commit to compare with. Defaults to None.

        Returns:
            str: The diff between the specified commit and the current branch, or None if the diff cannot be generated.
        """
        try:
            remote_branch = self.repo.remotes.origin.refs[self.repo.active_branch.name]
            diff = self.repo.git.diff(commit if commit else remote_branch.commit)
            return diff
        except Exception as e:
            return None

    def is_branch_available_on_remote(self, remote='origin', branch=None):
        """
        Checks if the specified branch is available on the remote.

        Args:
            remote (str, optional): The name of the remote. Defaults to 'origin'.
            branch (str, optional): The name of the branch. Defaults to None (current branch).

        Returns:
            bool: True if the branch is available on the remote, False otherwise.
        """
        try:
            if branch is None:
                current_branch = self.repo.active_branch
            else:
                current_branch = self.repo.branches[branch]
            remote_branches = self.repo.remotes[remote].refs
            return current_branch.name in remote_branches
        except:
            return False

    def is_commit_available_on_remote(self, commit):
        """
        Checks if the specified commit is available on the remote.

        Args:
            commit (str): The SHA hash of the commit.

        Returns:
            bool: True if the commit is available on the remote, False otherwise.
        """
        try:
            remote_branches = self.repo.remotes.origin.refs
            for branch in remote_branches:
                if commit in self.repo.git.rev_list(branch):
                    return True
            return False
        except:
            return False

    def get_git_root(self, path):
        """
        Retrieves the root directory of the Git repository.

        Args:
            path (str): The path to a file or directory within the repository.

        Returns:
            str: The relative path from the specified path to the root directory of the repository, or None if the root directory cannot be determined.
        """
        try:
            git_root = self.repo.git.rev_parse("--show-toplevel")
            relative_path = os.path.relpath(path, git_root)
            return relative_path
        except:
            return None
