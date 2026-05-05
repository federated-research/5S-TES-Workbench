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

- **Python 3.11+** installed
- **`five-safes-tes-workbench`** package installed in your environment:
    
    ```bash
    pip install five-safes-tes-workbench
    ```
    
- Access to a running **TES endpoint**
- Access to a **MinIO** instance with an output bucket configured
- Valid **authentication credentials** either a pre-obtained access token or Keycloak client/user credentials provided by your TRE administrator


## Validation

Before building or submitting any task, you must validate your configuration and credentials by calling `wb.validate()`.

The first step will be importing the workbench from the pip package as follows and initialize the client.

```
from five_safes_tes_workbench.workbench import Workbench

wb = Workbench()
```

### Required Params

This section explains the required parameters to validate the user before building the TES message and submitting into the submission layer of the 5S-TES. 

The required parameters are structured into two types. 

- **Config Params:** The configuration parameters are required to establish a connection to the TES endpoint, MinIO storage and define which TREs the task will be submitted to.

| Parameter | Description |
| --- | --- |
| project | Project name |
| tes_base_url | Base URL of the TES service |
| minio_sts_endpoint | MinIO STS endpoint URL |
| minio_endpoint | MinIO endpoint URL |
| minio_output_bucket | MinIO output bucket name |
| tres | List of TRE names to target |


- **Auth Params:** The authentication parameters are required to authenticate via ID Provider (Keycloak) and fetch the access token.

You can either provide Keycloak Credentials or Direct Access Key

| Parameter | Description |
| --- | --- |
| access_token | Pre-obtained access token from the Submission UI |
| client_id / client_secret | Keycloak client credentials |
| username / password | Keycloak user credentials |
| keycloak_url | Keycloak base URL |


### Option A - Direct Params

The next step is to validate the user using the required parameters. There are two ways to provide your configuration for validation: 

Parse the parameters directly as a keyword arguments. There are two further ways to do it. 

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

### Option B - **YAML Config File**

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