from pydantic import BaseModel


class MessageSerializer(BaseModel):
    """
    A Message request body fields.
    """

    content: str
    attachments: list = None
