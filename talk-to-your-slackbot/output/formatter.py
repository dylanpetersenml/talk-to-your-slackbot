"""
Output formatter: structures analysis results into a concise message for Slack.

Incorporates engine response and optional prior Memory context for
contextual coaching insights.
"""

from .models import FormatterInput, FormattedOutput


# Slack-friendly section headers (short, no markdown that might break).
_INSIGHT_HEADER = "Coaching insight"
_CONTEXT_HEADER = "Context from past matches"
_ERROR_HEADER = "Something went wrong"


def format_for_slack(input_data: FormatterInput) -> FormattedOutput:
    """
    Structure engine analysis (and optional Memory) into a concise Slack message.

    Parameters
    ----------
    input_data : FormatterInput
        Engine response and/or error, plus optional memory_context.

    Returns
    -------
    FormattedOutput
        A single slack_message string suitable for posting in a channel.
    """
    parts = []

    if input_data.error:
        parts.append(f"*{_ERROR_HEADER}*\n{input_data.error.strip()}")
    elif input_data.engine_response:
        parts.append(f"*{_INSIGHT_HEADER}*\n{input_data.engine_response.strip()}")
    else:
        parts.append(
            "*{header}*\nI couldn't produce an analysis for this match. "
            "Check that stats are loaded and try rephrasing your question.".format(
                header=_ERROR_HEADER
            )
        )

    if input_data.memory_context and input_data.memory_context.strip():
        memory_text = input_data.memory_context.strip()
        if memory_text and not input_data.error:
            parts.append(f"*{_CONTEXT_HEADER}*\n{memory_text}")

    slack_message = "\n\n".join(parts)
    return FormattedOutput(slack_message=slack_message)
