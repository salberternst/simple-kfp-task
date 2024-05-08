#!/usr/bin/env python
from simple_kfp_task.task import Task
from argparse import ArgumentParser


def main():
    """
    Entry point of the program.
    
    Parses command line arguments and calls the `run` function with the parsed arguments.
    """
    
    parser = ArgumentParser()
    parser.add_argument('command')
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--experiment-name")
    parser.add_argument("--run-name")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--remote-url")
    parser.add_argument("--branch")
    parser.add_argument("--commit")
    parser.add_argument("--ignore-ssh-error")
    parser.add_argument("--requirements")
    parser.add_argument("--packages", nargs='+', default=[])
    parser.add_argument("--gpu-limit", default=0)
    parser.add_argument("--cpu-limit", default="1")
    parser.add_argument("--cpu-request", default="0.5")
    parser.add_argument("--memory-limit", default="2Gi")
    parser.add_argument("--memory-request", default="1Gi")
    parser.add_argument("--gpu-vendor", default="nvidia.com/gpu")
    parser.add_argument("--container-image", default="python:3.12.3-slim")
    parser.add_argument("--volume-name", default=None)
    parser.add_argument("--disable-git-detection", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--wait-for-run", action="store_true", default=False)
    parser.add_argument("--kfp-host", default="https://10-101-20-33.sslip.io")
    parser.add_argument("--verify-ssl", action="store_true", default=False)

    args, command_args = parser.parse_known_args()

    task = Task.init(
        run_name=args.run_name,
        experiment_name=args.experiment_name,
        namespace=args.namespace,
        command=args.command,
        args=command_args,
        remote=args.remote,
        remote_url=args.remote_url,
        branch=args.branch,
        commit=args.commit,
        requirements=args.requirements,
        packages=args.packages,
        gpu_limit=args.gpu_limit,
        gpu_vendor=args.gpu_vendor,
        cpu_limit=args.cpu_limit,
        cpu_request=args.cpu_request,
        memory_limit=args.memory_limit,
        memory_request=args.memory_request,
        volume_name=args.volume_name,
        container_image=args.container_image,
        kfp_host=args.kfp_host,
        verify_ssl=args.verify_ssl,
    )

    if not args.dry_run:
        run = task.run()
        if args.wait_for_run:
            run_response = run.wait_for_run_completion()
            run = run_response.run.id
            print(run_response)
