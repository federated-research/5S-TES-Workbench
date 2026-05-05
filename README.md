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