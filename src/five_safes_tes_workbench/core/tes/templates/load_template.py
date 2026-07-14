from pathlib import Path
from importlib.resources import files

from ....common.params.tes_builder_params import TESTaskParams

def load_template(path: Path) -> TESTaskParams:
    with open(path) as f:
        return TESTaskParams.model_validate_json(f.read())

# def load_hello_world_template

def load_library_template(name: str) -> TESTaskParams:
    template_dir = files("five_safes_tes_workbench.core.tes.templates")
    template_file = (template_dir / f"{name}.json").read_text()
    template = TESTaskParams.model_validate_json(template_file)

    return template

def load_bunny_template(task_name: str = "Bunny task") -> TESTaskParams:
    template = load_library_template("bunny")
    template.name = task_name

    return template
