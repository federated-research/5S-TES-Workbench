from enum import IntEnum


class TaskStatus(IntEnum):
    """
    Enum for task status codes with their corresponding display names.
    source: https://github.com/SwanseaUniversityMedical/5s-Tes/blob/main/Shared/FiveSafesTes.Core/Models/Enums/Enums.cs
    """

    # Parent only
    WAITING_FOR_CHILD_SUBS_TO_COMPLETE = 0
    # Stage 1
    WAITING_FOR_AGENT_TO_TRANSFER = 1
    # Stage 2
    TRANSFERRED_TO_POD = 2
    # Stage 3
    POD_PROCESSING = 3
    # Stage 3 - Green
    POD_PROCESSING_COMPLETE = 4
    # Stage 4
    DATA_OUT_APPROVAL_BEGUN = 5
    # Stage 4 - Red
    DATA_OUT_APPROVAL_REJECTED = 6
    # Stage 4 - Green
    DATA_OUT_APPROVED = 7
    # Stage 1 - Red
    USER_NOT_ON_PROJECT = 8
    # Stage 2 - Red
    INVALID_USER = 9
    # Stage 2 - Red
    TRE_NOT_AUTHORISED_FOR_PROJECT = 10
    # Stage 5 - Green (completed enum)
    COMPLETED = 11
    # Stage 1 - Red
    INVALID_SUBMISSION = 12
    # Stage 1 - Red
    CANCELLING_CHILDREN = 13
    # Stage 1 - Red
    REQUEST_CANCELLATION = 14
    # Stage 1 - Red
    CANCELLATION_REQUEST_SENT = 15
    # Stage 5 - Red
    CANCELLED = 16
    # Stage 1
    SUBMISSION_WAITING_FOR_CRATE_FORMAT_CHECK = 17
    # Unused
    VALIDATING_USER = 18
    # Unused
    VALIDATING_SUBMISSION = 19
    # Unused - Green
    VALIDATION_SUCCESSFUL = 20
    # Stage 2
    AGENT_TRANSFERRING_TO_POD = 21
    # Stage 2 - Red
    TRANSFER_TO_POD_FAILED = 22
    # Unused
    TRE_REJECTED_PROJECT = 23
    # Unused
    TRE_APPROVED_PROJECT = 24
    # Stage 3 - Red
    POD_PROCESSING_FAILED = 25
    # Stage 1 - Parent only
    RUNNING = 26
    # Stage 5 - Red
    FAILED = 27
    # Stage 2
    SENDING_SUBMISSION_TO_HUTCH = 28
    # Stage 4
    REQUESTING_HUTCH_DOES_FINAL_PACKAGING = 29
    # Stage 3
    WAITING_FOR_CRATE = 30
    # Stage 3
    FETCHING_CRATE = 31
    # Stage 3
    QUEUED = 32
    # Stage 3
    VALIDATING_CRATE = 33
    # Stage 3
    FETCHING_WORKFLOW = 34
    # Stage 3
    STAGING_WORKFLOW = 35
    # Stage 3
    EXECUTING_WORKFLOW = 36
    # Stage 3
    PREPARING_OUTPUTS = 37
    # Stage 3
    DATA_OUT_REQUESTED = 38
    # Stage 3
    TRANSFERRED_FOR_DATA_OUT = 39
    # Stage 3
    PACKAGING_APPROVED_RESULTS = 40
    # Stage 3 - Green
    COMPLETE = 41
    # Stage 3 - Red
    FAILURE = 42
    # Stage 1
    SUBMISSION_RECEIVED = 43
    # Stage 1 - Green
    SUBMISSION_CRATE_VALIDATED = 44
    # Stage 1 - Red
    SUBMISSION_CRATE_VALIDATION_FAILED = 45
    # Stage 2 - Green
    TRE_CRATE_VALIDATED = 46
    # Stage 2 - Red
    TRE_CRATE_VALIDATION_FAILED = 47
    # Stage 2
    TRE_WAITING_FOR_CRATE_FORMAT_CHECK = 48
    # Stage 5 - Green - Parent Only
    PARTIAL_RESULT = 49


# Status lookup dictionary for easy access to display names
TASK_STATUS_DESCRIPTIONS = {
    TaskStatus.WAITING_FOR_CHILD_SUBS_TO_COMPLETE: "Waiting for Child Submissions To Complete",
    TaskStatus.WAITING_FOR_AGENT_TO_TRANSFER: "Waiting for Agent To Transfer",
    TaskStatus.TRANSFERRED_TO_POD: "Transferred To Pod",
    TaskStatus.POD_PROCESSING: "Pod Processing",
    TaskStatus.POD_PROCESSING_COMPLETE: "Pod Processing Complete",
    TaskStatus.DATA_OUT_APPROVAL_BEGUN: "Data Out Approval Begun",
    TaskStatus.DATA_OUT_APPROVAL_REJECTED: "Data Out Rejected",
    TaskStatus.DATA_OUT_APPROVED: "Data Out Approved",
    TaskStatus.USER_NOT_ON_PROJECT: "User Not On Project",
    TaskStatus.INVALID_USER: "User not authorised for project on TRE",
    TaskStatus.TRE_NOT_AUTHORISED_FOR_PROJECT: "TRE Not Authorised For Project",
    TaskStatus.COMPLETED: "Completed",
    TaskStatus.INVALID_SUBMISSION: "Invalid Submission",
    TaskStatus.CANCELLING_CHILDREN: "Cancelling Children",
    TaskStatus.REQUEST_CANCELLATION: "Request Cancellation",
    TaskStatus.CANCELLATION_REQUEST_SENT: "Cancellation Request Sent",
    TaskStatus.CANCELLED: "Cancelled",
    TaskStatus.SUBMISSION_WAITING_FOR_CRATE_FORMAT_CHECK: "Waiting For Crate Format Check",
    TaskStatus.VALIDATING_USER: "Validating User",
    TaskStatus.VALIDATING_SUBMISSION: "Validating Submission",
    TaskStatus.VALIDATION_SUCCESSFUL: "Validation Successful",
    TaskStatus.AGENT_TRANSFERRING_TO_POD: "Agent Transferring To Pod",
    TaskStatus.TRANSFER_TO_POD_FAILED: "Transfer To Pod Failed",
    TaskStatus.TRE_REJECTED_PROJECT: "Tre Rejected Project",
    TaskStatus.TRE_APPROVED_PROJECT: "Tre Approved Project",
    TaskStatus.POD_PROCESSING_FAILED: "Pod Processing Failed",
    TaskStatus.RUNNING: "Running",
    TaskStatus.FAILED: "Failed",
    TaskStatus.SENDING_SUBMISSION_TO_HUTCH: "Sending submission to Hutch",
    TaskStatus.REQUESTING_HUTCH_DOES_FINAL_PACKAGING: "Requesting Hutch packages up final output",
    TaskStatus.WAITING_FOR_CRATE: "Waiting for a Crate",
    TaskStatus.FETCHING_CRATE: "Fetching Crate",
    TaskStatus.QUEUED: "Crate queued",
    TaskStatus.VALIDATING_CRATE: "Validating Crate",
    TaskStatus.FETCHING_WORKFLOW: "Fetching workflow",
    TaskStatus.STAGING_WORKFLOW: "Preparing workflow",
    TaskStatus.EXECUTING_WORKFLOW: "Executing workflow",
    TaskStatus.PREPARING_OUTPUTS: "Preparing outputs",
    TaskStatus.DATA_OUT_REQUESTED: "Requested Egress",
    TaskStatus.TRANSFERRED_FOR_DATA_OUT: "Waiting for Egress results",
    TaskStatus.PACKAGING_APPROVED_RESULTS: "Finalising approved results",
    TaskStatus.COMPLETE: "Completed",
    TaskStatus.FAILURE: "Failed",
    TaskStatus.SUBMISSION_RECEIVED: "Submission has been received",
    TaskStatus.SUBMISSION_CRATE_VALIDATED: "Crate Validated",
    TaskStatus.SUBMISSION_CRATE_VALIDATION_FAILED: "Crate Failed Validation",
    TaskStatus.TRE_CRATE_VALIDATED: "Crate Validated",
    TaskStatus.TRE_CRATE_VALIDATION_FAILED: "Crate Failed Validation",
    TaskStatus.TRE_WAITING_FOR_CRATE_FORMAT_CHECK: "Waiting For Crate Format Check",
    TaskStatus.PARTIAL_RESULT: "Complete but not all TREs returned a result",
}
