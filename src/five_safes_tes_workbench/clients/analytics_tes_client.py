import tes  # type: ignore

from five_safes_tes_workbench.clients import base_tes_client


class AnalyticsTES(base_tes_client.BaseTESClient):
    #### this section will be implemented for each type of task using the pytes classes. Note that many of these fields are set in the submission layer after submission.
    def set_inputs(self) -> None:
        """
        Set the inputs for a TES task.
        """
        self.inputs = None
        return None

    def set_outputs(
        self,
        name: str,
        output_path: str,
        output_type: str = "DIRECTORY",
        description: str = "",
        url="",
    ) -> None:
        """
        Set the outputs for a TES task.
        """
        self.outputs = [
            tes.Output(
                path=output_path,
                type=output_type,
                name=name,
                description=description,
                url=url,
            )
        ]
        return None

    def _set_env(self) -> None:
        """
        Set the environment variables for a TES task.
        """
        self.env = {
            "postgresDatabase": self.default_db_config["name"],
            "postgresServer": self.default_db_config["host"],
            "postgresPassword": self.default_db_config["password"],
            "postgresUsername": self.default_db_config["username"],
        }
        return None

    def _set_command(
        self,
        query: str,
        analysis_type: str,
        output_path: str,
        output_format: str = "json",
    ) -> None:
        """
        Set the command for a TES task.
        """

        self.command = [
            f"--user-query={query}",
            f"--analysis={analysis_type}",
            f"--output-filename={output_path}/output",
            f"--output-format={output_format}",
        ]
        ## add this one if you want to override the injected connection vars with a command line argument.
        # connection_string = f"postgresql://postgres:{self.default_db_config['password']}@{self.default_db_config['host']}:{self.default_db_config['port']}/{self.default_db_config['name']}"
        # f"--db-connection={connection_string}",
        return None

    def set_executors(
        self,
        query,
        analysis_type,
        workdir="/app",
        output_path="/outputs",
        output_format="json",
    ) -> None:
        """
        Set the executors for a TES task.
        """
        self._set_command(query, analysis_type, output_path, output_format)
        self._set_env()
        self.executors = [
            tes.Executor(
                image=self.default_image,
                command=self.command,
                env=self.env,
                workdir=workdir,
            )
        ]
        return None

    def set_tes_messages(
        self,
        query: str,
        analysis_type: str,
        task_name: str = "test",
        task_description: str = "",
        output_format: str = "json",
    ) -> None:
        """
        Set the TES message for a TES task.
        """
        self.set_inputs()
        self.set_outputs(name="", output_path="/outputs", output_type="DIRECTORY")
        self.set_executors(
            query=query,
            analysis_type=analysis_type,
            workdir="/app",
            output_path="/outputs",
            output_format=output_format,
        )
        self.create_tes_message(
            task_name=task_name, task_description=task_description or ""
        )
        self.create_FiveSAFES_TES_message()
        return None
