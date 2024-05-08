import os
from simple_kfp_task.deploykf import create_kfp_client
from typing import Callable
from simple_kfp_task.pipeline import simple_task_pipeline
from simple_kfp_task.utils import encode_string_to_base64, get_caller_filename
from simple_kfp_task.git_helper import GitHelper

GIT_DIFF_MAX_LENGTH = 10000
PIP_PACKAGE_NAME = "simple-kfp-task-stub"


class Task:
    """
    Represents a task to be executed in a Kubeflow Pipelines (KFP) environment.

    Args:
        namespace (str, optional): The namespace in which to run the task. Defaults to None.
        run_name (str, optional): The name of the KFP run. Defaults to None.
        experiment_name (str, optional): The name of the KFP experiment. Defaults to None.
        func (Callable, optional): The function to be executed as part of the task. Defaults to None.
        command (str, optional): The command to be executed in the task. Defaults to None.
        args (List[str], optional): The arguments to be passed to the command. Defaults to None.
        cwd (str, optional): The current working directory for the task. Defaults to None.
        remote (str, optional): The name of the remote repository. Defaults to 'origin'.
        remote_url (str, optional): The URL of the remote repository. Defaults to None.
        branch (str, optional): The branch to be used for the task. Defaults to None.
        commit (str, optional): The commit to be used for the task. Defaults to None.
        requirements (str, optional): The path to the requirements file for the task. Defaults to None.
        packages (List[str], optional): The additional Python packages required for the task. Defaults to [].
        container_image (str, optional): The Docker container image to be used for the task. Defaults to 'python:3.12.3-slim'.
        gpu_limit (int, optional): The GPU limit for the task. Defaults to 0.
        gpu_vendor (str, optional): The GPU vendor for the task. Defaults to 'nvidia.com/gpu'.
        cpu_limit (str, optional): The CPU limit for the task. Defaults to "1".
        cpu_request (str, optional): The CPU request for the task. Defaults to "0.5".
        memory_limit (str, optional): The memory limit for the task. Defaults to "2Gi".
        memory_request (str, optional): The memory request for the task. Defaults to "1Gi".
        volume_name (str, optional): The name of the volume to be used for the task. Defaults to None.

    Raises:
        ValueError: If the command is not provided or does not exist.
        ValueError: If the branch is not available on the remote repository.
        ValueError: If the Git diff is too long. Please commit and push your changes first.

    """

    def __init__(
        self,
        kfp_host = "https://10-101-20-33.sslip.io",
        verify_ssl = False,
        namespace: str = None,
        run_name: str = None,
        experiment_name: str = None,
        func: Callable = None,
        command=None,
        args=None,
        cwd=None,
        remote='origin',
        remote_url=None,
        branch=None,
        commit=None,
        requirements=None,
        packages=[],
        container_image='python:3.12.3-slim',
        gpu_limit=0,
        gpu_vendor='nvidia.com/gpu',
        cpu_limit="1",
        cpu_request="0.5",
        memory_limit="2Gi",
        memory_request="1Gi",
        volume_name=None
    ):
        self.namespace = namespace
        self.run_name = run_name
        self.experiment_name = experiment_name
        self.func = func
        self.command = command
        self.args = args
        self.cwd = cwd
        self.remote = remote
        self.remote_url = remote_url
        self.branch = branch
        self.commit = commit
        self.requirements = requirements
        self.packages = packages
        self.container_image = container_image
        self.gpu_limit = gpu_limit
        self.gpu_vendor = gpu_vendor
        self.cpu_limit = cpu_limit
        self.cpu_request = cpu_request
        self.memory_limit = memory_limit
        self.memory_request = memory_request
        self.volume_name = volume_name
        self.kfp_host = kfp_host
        self.verify_ssl = verify_ssl

        git_helper = GitHelper()

        if self.func:
            self.command = os.path.relpath(get_caller_filename(), os.getcwd())
            if self.packages is None:
                self.packages = [PIP_PACKAGE_NAME]
            else:
                self.packages.append(PIP_PACKAGE_NAME)

        if not self.cwd:
            self.cwd = f'/app/{git_helper.get_git_root(os.getcwd())}'

        if not self.command:
            raise ValueError("Command is required.")
        
        if not os.path.exists(self.command):
            raise ValueError(f"Command {self.command} does not exist.")
        
        if self.remote_url is None:
            self.remote_url = git_helper.get_remote_url(self.remote)

        if not self.branch:
            self.branch = git_helper.get_current_branch()

        if not git_helper.is_branch_available_on_remote(remote=self.remote, branch=self.branch):
            raise ValueError(f"Branch {self.branch} is not available on remote")

        if not self.commit:
            self.commit = git_helper.get_current_commit()

        self.git_diff = None
        if not git_helper.is_commit_available_on_remote(self.commit) or git_helper.is_git_dirty():
            self.git_diff = encode_string_to_base64(git_helper.build_git_diff())

        if self.git_diff and len(self.git_diff) > GIT_DIFF_MAX_LENGTH:
            raise ValueError(f"Git diff is too long {len(self.git_diff)}. Please commit and push your changes first.")

    @classmethod
    def init(cls, **kwargs):
        """
        Initialize a Task object with the provided keyword arguments.

        Args:
            **kwargs: The keyword arguments to be passed to the Task constructor.

        Returns:
            Task: The initialized Task object.

        """
        return cls(**kwargs)

    def run(self):
        """
        Run the task using the provided configuration.

        Returns:
            kfp_client.create_run_from_pipeline_func: The KFP run created for the task.

        """
        kfp_client = create_kfp_client(namespace=self.namespace, host=self.kfp_host, verify_ssl=self.verify_ssl)
        return kfp_client.create_run_from_pipeline_func(
            pipeline_func=simple_task_pipeline,
            experiment_name=self.experiment_name,
            run_name=self.run_name,
            arguments={
                "command": self.command if self.command else "",
                "args": " ".join(self.args) if self.args else "",
                "cwd": self.cwd,
                "remote_url": self.remote_url,
                "branch": self.branch,
                "commit": self.commit,
                "git_diff": self.git_diff if self.git_diff else "",
                "requirements": self.requirements if self.requirements else "",
                "packages": " ".join(self.packages) if self.packages else "",
                "gpu_limit": self.gpu_limit,
                "gpu_vendor": self.gpu_vendor,
                "cpu_limit": self.cpu_limit,
                "cpu_request": self.cpu_request,
                "memory_limit": self.memory_limit,
                "memory_request": self.memory_request,
                "volume_name": self.volume_name if self.volume_name else "",
                "container_image": self.container_image
            }
        )

   
    
    