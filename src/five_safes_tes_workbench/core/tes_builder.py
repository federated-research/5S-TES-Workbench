import tes  # type: ignore

from ..schema.config_schema import ConfigValidationModel
from ..utils.logger import get_logger
from ..common.tes_builder_params import TESTaskParams
from datetime import datetime, timezone

logger = get_logger(__name__)

# ----- Defaults ------

_DEFAULT_NAME = "Hello World"
_DEFAULT_DESCRIPTION = "Hello World"
_DEFAULT_OUTPUT_URL = "s3://"
_DEFAULT_OUTPUT_PATH = "/outputs"

class WorkbenchTESBuilder:
    """
    Builder class responsible for constructing TES tasks
    based on the validated configuration and 
    provided TES task parameters.
    """

    def __init__(self) -> None:
        """
        Initializes the WorkbenchTESBuilder with a 
        placeholder for the TES task that will
        be built during the build process.
        """
        self._tes_task: tes.Task | None = None

    @property
    def tes_task(self) -> tes.Task:
        """
        Returns the built TES task.
        """
        if self._tes_task is None:
            raise ValueError("Before submitting the TES message, please call the function build_tes().")
        return self._tes_task

    def build(
        self,
        config: ConfigValidationModel,
        params: TESTaskParams,
    ) -> None:
        """
        Builds the TES task based on the provided configuration
        and TES task parameters.
        
        Parameters
        ----------
        - config: Validated configuration containing TES endpoint
          and other settings.
          
        - params: Parameters for building the TES task. TESTaskParams
        holds the expected params for both config
        and tes message.
        """

        name = params.get("name", _DEFAULT_NAME)
        description = params.get("description", _DEFAULT_DESCRIPTION)
        image = params["image"]
        command = params["command"]
        output_url = params.get("output_url", _DEFAULT_OUTPUT_URL)
        output_path = params.get("output_path", _DEFAULT_OUTPUT_PATH)

        self._tes_task = tes.Task(
            name=name,
            description=description,
            inputs=[],
            outputs=[
                tes.Output(
                    name="Stdout",
                    description="Stdout results",
                    url=output_url,
                    path=output_path,
                    type="DIRECTORY",
                )
            ],
            executors=[tes.Executor(image=image, command=command)],
            volumes=None,
            tags={
                "project": config.project,
                "tres": ",".join(config.tres),
            },
            logs=None,
            creation_time=datetime.now(timezone.utc),
        )

        task_json_pretty: str = self._tes_task.as_json(indent=3)  # type: ignore[reportUnknownMemberType]
        logger.info("TES Task built successfully")
        logger.info("TES payload:\n%s", task_json_pretty)