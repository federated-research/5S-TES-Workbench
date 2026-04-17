import time
from typing import List

from five_safes_tes_workbench.clients.base_tes_client import get_status_description


class Polling:
    def __init__(self, tes_client, minio_client, task_id: str):
        self.tes_client = tes_client
        self.minio_client = minio_client
        self.end_statuses = [11, 27, 16, 49]
        self.result_statuses = [11, 49]  ## completed or partial
        self.task_id = task_id
        self.poll_task = False
        self.poll_minio = False

        self.status = None
        self.status_description = None
        self.data = None

    def poll_task_status(self, polling_interval: int = 10):
        self.poll_task = True
        while self.poll_task:
            task_info = self.tes_client.get_task_status(self.task_id)
            status = task_info["status"]
            status_description = get_status_description(status)
            print(f"Task status: {status} - {status_description}")
            ## check for completed, failed, running, or cancelled statuses - i.e., job is done
            if status in self.end_statuses:
                self.poll_task = False
                self.status = status
                self.status_description = status_description
                return status, status_description
            time.sleep(polling_interval)

    def poll_minio_results(
        self,
        results_paths: List[str],
        bucket: str,
        n_results: int = 1,
        polling_interval: int = 10,
    ) -> List[str]:
        """
        Collect results from MinIO storage.

        Args:
            results_paths (List[str]): List of paths to collect results from
            bucket (str): MinIO bucket name
            n_results (int): Expected number of results. It will poll until it has at least n_results, but will check all paths so may return more.

        Returns:
            List[str]: Collected data from all sources
        """
        data = []
        self.poll_minio = True
        while self.poll_minio:
            data = []
            for results_path in results_paths:
                result = self.minio_client.get_object_smart(bucket, results_path)
                if result:
                    data.append(result)

            if n_results is not None and len(data) < n_results:
                print(f"Waiting for results... ({len(data)}/{n_results} received)")
                time.sleep(polling_interval)
            else:
                self.poll_minio = False
                print(f"{len(data)} results collected successfully")
                self.data = data
                return data

    def poll_results(
        self,
        results_paths: List[str],
        bucket: str,
        n_results: int = 1,
        polling_interval: int = 10,
    ) -> List[str]:
        status, status_description = self.poll_task_status(polling_interval)
        if status in self.result_statuses:
            ## how many results are we looking for? We're only going to check once, but get all that's available

            return self.poll_minio_results(
                results_paths, bucket, n_results, polling_interval
            )
        else:
            return None
