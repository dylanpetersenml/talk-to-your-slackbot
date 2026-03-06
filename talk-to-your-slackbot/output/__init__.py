"""
Output subsystem: format engine results for Slack and apply delivery guardrails.

Structures analysis (and optional prior Memory context) into a concise
message and ensures accuracy and safety before delivery.
"""

from .models import FormatterInput, FormattedOutput, OutputRejection
from .formatter import format_for_slack
from .guardrails import apply_output_guardrails
from .slack_sender import SendResult, send_output_to_slack, send_to_slack


def process_output(input_data: FormatterInput) -> FormattedOutput | OutputRejection:
    """
    Run the full output pipeline: format for Slack then apply output guardrails.

    Parameters
    ----------
    input_data : FormatterInput
        Engine response and/or error, plus optional memory_context.

    Returns
    -------
    FormattedOutput | OutputRejection
        Message ready for Slack, or a rejection with a user-safe reason.
    """
    formatted = format_for_slack(input_data)
    return apply_output_guardrails(formatted)


__all__ = [
    "process_output",
    "format_for_slack",
    "apply_output_guardrails",
    "send_to_slack",
    "send_output_to_slack",
    "SendResult",
    "FormatterInput",
    "FormattedOutput",
    "OutputRejection",
]
