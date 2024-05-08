from simple_kfp_task import Task

def run():
    from train import train
    import os 

    os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "true"

    train()


if __name__ == "__main__":
    task = Task.init(
        func=run,
        packages=[ "mlflow>=2.0", "tensorflow>=2.8", "psutil", "pynvml" ],
        namespace="sebastian-alberternst",
        remote_url="https://github.com/salberternst/simple-kfp-task.git",
        container_image="tensorflow/tensorflow:2.8.4-gpu",
        memory_limit="4Gi",
        gpu_limit=1
    )

    task.run()