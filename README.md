# User Guide - 5S-TES-Workbench

This is the user guide for using the Workbench within a Jupyter Notebook to make analysis submissions and retrieve results from the submission layer.

The Workbench is a Python-based library which provides a simple interface for submitting computational tasks to a Task Execution Service (TES) endpoint within a Five Safes federated research environment. It handles configuration validation, authentication, TES task construction, and result retrieval allowing researchers to focus on their analysis rather than the underlying infrastructure.

The typical workflow consists of four steps:

- **Validate:** Provide your infrastructure configuration and credentials.
- **Build:** Choose a task template and supply your analysis parameters.
- **Submit:** Send the task to the TES endpoint.
- **Pool Results:** Fetch output files from MinIO storage once the task completes.


## Pre-Requisites

Before using the Workbench, ensure you have the following:

- **Python 3.13+** installed
- **`five-safes-tes-workbench`** package installed in your environment:
    
    ```bash
    pip install five-safes-tes-workbench
    ```
    
- Access to a running **TES endpoint**
- Access to a **MinIO** instance with an output bucket configured
- Valid **authentication credentials**, which are either a pre-obtained access token from Submission Layer UI or Submission API's Keycloak credentials provided by Submission layer's administrator

## Initialize the Workbench

The first step will be importing the workbench from the pip package as follows and initialize the client.

```
from five_safes_tes_workbench.workbench import Workbench

wb = Workbench()
```

## Validation

Before building or submitting any task, you must validate your configuration and credentials by calling `wb.validate()`.


### Required Params

This section explains the required parameters to validate the user before building the TES message and submitting into the submission layer of the 5S-TES. 

The required parameters are structured into two types. 

#### Config Params

 The configuration parameters are required to establish a connection to the TES endpoint, MinIO storage and define which TREs the task will be submitted to.

    | Parameter | Description |
    | --- | --- |
    | project | Project name |
    | tes_base_url | Base URL of the TES service |
    | minio_sts_endpoint | MinIO STS endpoint URL |
    | minio_endpoint | MinIO endpoint URL |
    | minio_output_bucket | MinIO output bucket name |
    | tres | List of TRE names to target |

<br>

#### Auth Params

The authentication parameters are required to authenticate via ID Provider (Keycloak) and fetch the access token.

You can either provide Keycloak Credentials or Direct Access Key.

**Keycloak Credentials**

    | Parameter | Description |
    | --- | --- |
    | client_id / client_secret | Keycloak client credentials |
    | username / password | Keycloak user credentials |
    | keycloak_url | Keycloak base URL |

    
**Direct Access Token**

    | Parameter | Description |
    | --- | --- |
    | access_token | Pre-obtained access token from the Submission UI |


### Passing the Required Parameters into Workbench

The next step is to validate the user using the required parameters. There are two ways to provide your configuration for validation: 
- Option A - Direct Params
- Option B - Yaml Config File

#### Option A - Direct Params

Parse the parameters directly as a keyword arguments. There are two further ways to do it. 

<br>

- **Parsing the Configuration params and Authentication params**

```bash
wb.validate(
		# --- Config Params ---
    project="your-project-name",
    tes_base_url="http://your-tes-endpoint:5034",
    minio_sts_endpoint="http://your-minio-endpoint:9000/sts",
    minio_endpoint="http://your-minio-endpoint:9000",
    minio_output_bucket="your-output-bucket-name",
    tres=["Your-TRE1"],
    
    # --- Auth Params ---
    client_id="your-client-id",
    client_secret="your-client-secret",
    username="your-username",
    password="your-password",
    keycloak_url="http://your-keycloak-endpoint/",
)
```

<br>

- **Parsing the Configuration params and Access Token**

You can login to the submission layer [`https://5s-tes.federated-research.com/`](https://5s-tes.federated-research.com/) and authenticate yourself using keycloak credentials to get the api access token. 

Copy the access token and pass it into the `access_token` parameter. 

```bash
wb.validate(
		# --- Config Params ---
    project="your-project-name",
    tes_base_url="http://your-tes-endpoint:5034",
    minio_sts_endpoint="http://your-minio-endpoint:9000/sts",
    minio_endpoint="http://your-minio-endpoint:9000",
    minio_output_bucket="your-output-bucket-name",
    tres=["Your-TRE1"],
    
    # --- Auth Params ---
    access_token="your-access-token"
)
```

#### Option B - **YAML Config File**

Instead of passing the params directly as a keyword, you can create a .yaml file (which holds the Credentials and Authentication Params) and pass the path as a parameter within the validate. An example .yaml can be found here [[example-config.yml](example-config.yml)].

The workbench will extract the params from the yaml file and validate your credentials. 

```bash
wb.validate(config_path="path/to/your-config.yml")
```

- Example Yaml File:
```bash
# ----- Five Safes TES Workbench — Example Configuration ------

config:

  # ---- Required Configuration ----

  project: "your-project-name"
  tes_base_url: "http://localhost:5034"
  minio_sts_endpoint: "http://your-minio-endpoint:9000/sts"
  minio_endpoint: "your-minio-endpoint:9000"
  minio_output_bucket: "your-output-bucket-name"
  tres:
    - "Your-TRE1"
    - "Add more TREs as needed"


  auth:
    # ---- Option 1: Access Token ----
    # (Use Access Token if you have one from the Submission UI.)

    access_token: "your-access-token-here"

    # ---- Option 2: Keycloak Credentials ----
    # (Use Keycloak credentials if you want the Workbench to obtain an access token on your behalf.)

    client_id: "your-keycloak-client-id"
    client_secret: "your-keycloak-client-secret"
    username: "your-keycloak-username"
    password: "your-keycloak-password"
    keycloak_url: "http://localhost:your-keycloak-port/"
```


### **Build TES and Submit**

Once the Workbench has been validated, the next step is to build the TES task. 

The Workbench provides a template-based interface via `wb.build_tes.<template>(...)` which constructs the TES message that will be submitted to the endpoint.

**The available Templates are mentioned below:** 

| Template | Method | Use Case |
| --- | --- | --- |
| Hello World | build_tes.hello_world(...) | Verify the setup is working end-to-end |
| Simple SQL | build_tes.simple_sql(...) | Run a SQL query against a TRE database |
| Bunny | build_tes.bunny(...) | Run the Health Informatics Bunny CLI analytics tool |
| Custom | build_tes.custom(...) | Bring your own container image and command |


#### Hello World - wb.build_tes.hello_world( )

The simplest template. Every parameter is optional and can be called with no arguments at all and will fall back to sensible defaults. Use it to verify connectivity before running real analysis.

**Example Implementation**

```bash
# Minimal — no parameters needed
wb.build_tes.hello_world()

wb.submit()
```

#### Simple SQL - wb.build_tes.simple_sql( )

Executes a SQL query against a SQL database using the uses default image : `harbor.federated-analytics.ac.uk/5s-tes-analysis-tools/5s-tes-analysis-tools-tre-sqlpg:1.0.0`

| Parameters | Required  | Description |
| --- | --- | --- | --- |
| name | Yes | — | Task name |
| query | Yes | — | SQL query to execute |

**Example Implementation**

```bash
query = (
    'WITH user_query AS ('
    'SELECT value_as_number FROM "NottinghamDemo".measurement '
    'WHERE measurement_concept_id = 3000905 '
    'AND value_as_number IS NOT NULL'
    ') SELECT COUNT(*) AS n, SUM(value_as_number) AS total FROM user_query;'
)

wb.build_tes.simple_sql(
    name="Simple SQL Task",
    query=query,
)

wb.submit()
```


#### Bunny - wb.build_tes.bunny( )

Runs the Health Informatics Bunny CLI analytics container. The container image is fixed by the template: `ghcr.io/health-informatics-uon/five-safes-tes-analytics-bunny-cli:1.6.0`

 You provide the command list which is passed directly to the Bunny CLI. 

All the parameters in the bunny method can be overridden within the template. 

| Parameter | Required  | Description |
| --- | --- | --- |
| name | Yes | Task name |
| command | Yes | Arguments passed to the Bunny CLI |

**Example Implementation**

```bash
wb.build_tes.bunny(
    name="Bunny Task",
    command=[
        "--body-json",
        '{"code":"GENERIC","analysis":"DISTRIBUTION","uuid":"123","collection":"test","owner":"me"}',
        "--output",
        "/outputs/output.json",
        "--no-encode",
    ],
)

wb.submit()
```



#### Custom - wb.build_tes.custom( )

A fully user-defined task. `name`, `image`, and `command` are required. All other fields fall back to defaults if not provided.

All the parameters in the custom method can be overridden within the template. 

For more information about constructing a custom TES message, view [[the official schema of TES from GA4GH](https://ga4gh.github.io/task-execution-schemas/docs/#tag/TaskService/operation/CreateTask)].

**Example Implementation**

```bash
wb.build_tes.custom(
    name="Test Custom mode from Workbench",
    description="custom analysis",
    executors=[
        {
            "image": "ubuntu",
            "command": ["echo", "Hello World"],
            "workdir": "/outputs",
            "stdout": "/outputs/stdout"
        }
    ],
    outputs=[
        {
            "name": "Stdout",
            "description": "Stdout results",
            "url": "s3://",
            "path": "/outputs",
            "type": "DIRECTORY"
        }
    ],
)

wb.submit()
```

### **Collect Results**

Once a task has been submitted and completed, you can download the output files from MinIO storage using the fetch methods.

**Note:** The task must have reached a `Completed` status before fetching results.


#### **Output Directory Structure**

Downloaded files are saved in an output/ folder created **next to your notebook**, organised by TRE name and child task ID:

```bash
output/
└── <tre_name>/
    └── <child_task_id>/
        ├── output.json
        └── acro_output_20260501_085731.zip
```



#### Fetch Results - wb.fetch_outputs()

The `wb.fetch_output()` method will pool results from the TRE for the submissions made in the previous steps. This method works based on the parameters defined (see params table below).

| Parameter | Required | Description |
| --- | --- | --- |
| `tre` | No | TRE name to fetch results for. If omitted, results for **all TREs** in config are downloaded |
| `task_id` | No | Integer task ID. Defaults to the ID from the most recent `wb.submit()` call |
| `output_dir` | No | Local directory to write the downloaded files into. The directory (and any missing parents) is created automatically. Defaulted to the directory next to the notebook. |

- If `task_id` is not provided, the Workbench will automatically use the ID from the most recent `wb.submit()` call in the current session. 

- If no task has been submitted and no `task_id` is passed, the method will raise a `ValueError`.

<br>

**Example Implementation**
```python
# Fetch results for all TREs (uses last submitted task ID)
wb.fetch_outputs()

# Fetch results for a specific TRE
wb.fetch_outputs(tre="Nottingham TRE 01")

# Fetch with an explicit task ID (e.g. from a previous submission)
wb.fetch_outputs(task_id=945)

# Fetch for a specific TRE with an explicit task ID
wb.fetch_outputs(task_id=945, tre="Nottingham TRE 01")
```



#### **What to Expect**

Before downloading any files, the Workbench **first queries the submission layer** to check the current status of each child task (the per-TRE sub-task created when you called `wb.submit()`). Only tasks that have reached `Completed` status will have their files fetched from MinIO. Tasks that are still running or have terminated with an error are skipped.

You can also check the submission layer to see the progress of the submission [`https://5s-tes.federated-research.com/`](https://5s-tes.federated-research.com/).

**TRE behavior by state**

| Child Task State | Example Statuses | Behavior |
| --- | --- | --- |
| **In progress** | Running, Pod Processing, Waiting for Agent, Data Out Approval Begun... | Skipped: warning logged, no files downloaded for that TRE |
| **Terminated** | Failed, Cancelled, Data Out Rejected | Skipped: warning logged, no files downloaded for that TRE |
| **Completed** | Completed | Files downloaded from MinIO into `output/<tre>/<child_task_id>/` |

When fetching for **all TREs** (no `tre` argument passed), each TRE is evaluated independently. Completed TREs are downloaded straight away while in-progress or terminated TREs are skipped without affecting the others. You can re-run `wb.fetch_outputs()` at any point and previously downloaded TREs will be overwritten and any that were not yet complete will be retried.

**Example — single TRE, completed**

```bash
INFO | Child task info: 945, status: Completed
INFO | Fetching token from keycloak...
INFO | Keycloak token fetched successfully
INFO | Exchanging bearer token for MinIO credentials via STS
INFO | MinIO client initialised
INFO | Found 2 result object(s) for task 945
INFO | Downloading result object: 945/acro_output_20260501_085731.zip
INFO | Downloaded -> output/Nottingham TRE 01/945/acro_output_20260501_085731.zip
INFO | Downloading result object: 945/output.json
INFO | Downloaded -> output/Nottingham TRE 01/945/output.json
```


## Example Implementation (Jupyter Notebook)

A fully working notebook is available alongside this guide ([workbench-example.ipynb](src/five_safes_tes_workbench/notebooks/workbench-example.ipynb))

It contains ready-to-run cells covering all four steps: 
- validation
- building a TES task using each template 
- submitting
- fetching results

It is the quickest way to get started and verify your setup end-to-end. For a deeper explanation of any method, parameter, or behavior, refer back to this user guide.

