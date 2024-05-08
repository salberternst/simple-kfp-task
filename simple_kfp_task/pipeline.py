from kfp import dsl
from kubernetes import client as kubernetes_client


def run_command_op(name: str, container_image: str, command: str, args: str, cwd: str, branch: str, remote_url: str, requirements: str, packages: str, git_diff: str, commit: str):
    """
    Run a command inside a container using Kubernetes.

    Args:
        name (str): The name of the container operation.
        container_image (str): The container image to use for the operation.
        command (str): The command to run inside the container.
        args (str): The arguments to pass to the command.
        branch (str): The branch to clone from the remote repository.
        remote_url (str): The URL of the remote repository.
        requirements (str): The path to the requirements file for installing Python dependencies.
        packages (str): A space-separated string of additional packages to install.
        git_diff (str): The base64-encoded diff to apply to the cloned repository.
        commit (str): The commit to fetch from the remote repository.

    Returns:
        dsl.ContainerOp: The container operation object.
    """
    return dsl.ContainerOp(
        name=name,
        image=container_image,
        sidecars=[
            kubernetes_client.V1Container(
                name='git-clone',
                image='alpine/git:2.43.0',
                command=['sh', '-c'],
                args=[
                    f"""
touch /ipc/log && \
git clone --progress --single-branch --branch {branch} {remote_url} /app --depth=1 > /ipc/log 2>&1 && \
  cd /app && \
  git fetch --depth=1 origin {commit} > /ipc/log 2>&1 && \
  git checkout {commit} > /ipc/log 2>&1

git_clone_exit_code=$?
echo $git_clone_exit_code > /ipc/git-clone
if [ $git_clone_exit_code -ne 0 ]; then
    exit 1
fi

if [ -n "{git_diff}" ]; then
    cd /app && \
    echo '{git_diff}' | base64 -d | gunzip | git apply --verbose - > /ipc/log 2>&1
    git_apply_exit_code=$?
    echo $git_apply_exit_code > /ipc/git-apply
    if [ $git_apply_exit_code -ne 0 ]; then
        exit 1
    fi
fi
                    """
                ],
                volume_mounts=[
                    kubernetes_client.V1VolumeMount(
                        name='app-volume', mount_path='/app'),
                    kubernetes_client.V1VolumeMount(
                        name='ipc-volume', mount_path='/ipc')
                ],
            ),
        ],
        command=['sh', '-c'],
        arguments=[
            f"""
#
# Wait for the git clone to finish
#

touch /ipc/log
tail -F /ipc/log &
TAIL_PID=$!

until [ -f /ipc/git-clone ];
    do sleep 1;
done

if [ $(cat /ipc/git-clone) -ne 0 ]; then
    exit 1
fi

#
# Wait for the git apply to finish
#

if [ -n "{git_diff}" ]; then
    until [ -f /ipc/git-apply ]; do sleep 1; done
    if [ $(cat /ipc/git-apply) -ne 0 ]; then
        exit 1
    fi
fi

kill $TAIL_PID

cd {cwd} && \
if [ -n "{requirements}" ]; then pip install -r {requirements}; fi && \
if [ -n "{packages}" ]; then echo "{packages}" | xargs pip install; fi && \
python {command} {args}
            """
        ],
        container_kwargs={'working_dir': '/app'},
    ).add_volume(
        kubernetes_client.V1Volume(
            name="app-volume",
            empty_dir=kubernetes_client.V1EmptyDirVolumeSource()
        )
    ).add_volume(
        kubernetes_client.V1Volume(
            name="ipc-volume",
            empty_dir=kubernetes_client.V1EmptyDirVolumeSource()
        )
    ).add_volume_mount(
        kubernetes_client.V1VolumeMount(
            name='app-volume', mount_path='/app')
    ).add_volume_mount(
        kubernetes_client.V1VolumeMount(
            name='ipc-volume', mount_path='/ipc')
    ).add_env_variable(kubernetes_client.V1EnvVar(
        name="MLFLOW_TRACKING_URI", value="http://mlflow-server:5000"
    )).add_env_variable(kubernetes_client.V1EnvVar(
        name="MLFLOW_REGISTRY_URI", value="http://mlflow-server:5000"
    )).add_env_variable(kubernetes_client.V1EnvVar(
        name='INSIDE_KFP_FUNC_CONTAINER', value='true'))


@dsl.pipeline(
    name='Simple Task Pipeline',
    description='A simple pipeline that clones a Git repository, creates a virtual environment, runs pip, and executes a script.'
)
def simple_task_pipeline(
    remote_url: str = 'https://github.com/your/repo.git',
    branch: str = 'main',
    commit: str = 'HEAD',
    command: str = 'script.py',
    args: str = '',
    cwd: str = '/app',
    requirements: str = '',
    packages: str = '',
    gpu_limit: int = 0,
    gpu_vendor='nvidia.com/gpu',
    cpu_limit: str = "1",
    cpu_request: str = "0.5",
    memory_limit: str = '2Gi',
    memory_request: str = '1Gi',
    git_diff: str = '',
    container_image: str = 'python:3.12.3-slim',
    volume_name=''
):
    """
    Executes a simple task pipeline.

    Args:
        remote_url (str, optional): The URL of the remote repository. Defaults to 'https://github.com/your/repo.git'.
        branch (str, optional): The branch of the remote repository. Defaults to 'main'.
        commit (str, optional): The commit hash or reference of the remote repository. Defaults to 'HEAD'.
        command (str, optional): The command to be executed. Defaults to 'script.py'.
        command_args (str, optional): Additional arguments for the command. Defaults to ''.
        requirements (str, optional): Path to the requirements file. Defaults to ''.
        packages (str, optional): Additional packages to be installed. Defaults to ''.
        gpu_limit (int, optional): The GPU limit for the task. Defaults to 0.
        gpu_vendor (str, optional): The GPU vendor. Defaults to 'nvidia.com/gpu'.
        cpu_limit (str, optional): The CPU limit for the task. Defaults to '1'.
        cpu_request (str, optional): The CPU request for the task. Defaults to '0.5'.
        memory_limit (str, optional): The memory limit for the task. Defaults to '2Gi'.
        memory_request (str, optional): The memory request for the task. Defaults to '1Gi'.
        git_diff (str, optional): The git diff to be applied. Defaults to ''.
        container_image (str, optional): The container image to be used. Defaults to 'python:3.12.3-slim'.
        volume_name (str, optional): The name of the volume. Defaults to 'mlflow-pvc'.
    """

    with dsl.Condition(volume_name == ''):
        run_command_without_volume = run_command_op(
            name="Run Command Without Volume",
            container_image=container_image,
            command=command,
            args=args,
            cwd=cwd,
            remote_url=remote_url,
            branch=branch,
            requirements=requirements,
            packages=packages,
            git_diff=git_diff,
            commit=commit
        )

        run_command_without_volume.add_resource_request(gpu_vendor, gpu_limit)
        run_command_without_volume.add_resource_limit(gpu_vendor, gpu_limit)
        run_command_without_volume.add_resource_request('cpu', cpu_request)
        run_command_without_volume.add_resource_limit('cpu', cpu_limit)
        run_command_without_volume.add_resource_request(
            'memory', memory_request)
        run_command_without_volume.add_resource_limit('memory', memory_limit)

        run_command_without_volume.execution_options.caching_strategy.max_cache_staleness = "P0D"

    with dsl.Condition(volume_name != ''):
        run_command_with_volume = run_command_op(
            name="Run Command With Volume",
            container_image=container_image,
            command=command,
            args=args,
            cwd=cwd,
            remote_url=remote_url,
            branch=branch,
            requirements=requirements,
            packages=packages,
            git_diff=git_diff,
            commit=commit
        ).add_volume(
            kubernetes_client.V1Volume(
                name="data-volume",
                persistent_volume_claim=kubernetes_client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=volume_name)
            )
        ).add_volume_mount(
            kubernetes_client.V1VolumeMount(
                name="data-volume", mount_path='/volume'
            )
        )

        run_command_with_volume.add_resource_request(gpu_vendor, gpu_limit)
        run_command_with_volume.add_resource_limit(gpu_vendor, gpu_limit)
        run_command_with_volume.add_resource_request('cpu', cpu_request)
        run_command_with_volume.add_resource_limit('cpu', cpu_limit)
        run_command_with_volume.add_resource_request('memory', memory_request)
        run_command_with_volume.add_resource_limit('memory', memory_limit)

        run_command_with_volume.execution_options.caching_strategy.max_cache_staleness = "P0D"

    dsl.get_pipeline_conf().set_timeout(3600)
