from django.conf import settings
import slack


if settings.SLACK['api_token'] is None:
    raise ValueError("SLACK_API_TOKEN environment variable is required")


CREATE_SUPERUSER_MESSAGE = "`{username}` was granted superuser access"


def notify_superuser_created(username, by_username=None):
    message = CREATE_SUPERUSER_MESSAGE.format(username=username)
    if by_username:
        message = f"{message} by `{by_username}`"
    send_notification(message)


def send_notification(message):
    client = slack.WebClient(token=settings.SLACK['api_token'])
    client.chat_postMessage(
        channel=settings.SLACK["channel"],
        text=f"{message} [{settings.ENV}]",
    )
