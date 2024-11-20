from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UnicodeSetAttribute,
    UTCDateTimeAttribute,
    ListAttribute,
    BooleanAttribute,
    MapAttribute,
)
import os
from dotenv import load_dotenv
from datetime import datetime
from uuid import uuid4

# Load .env file
load_dotenv()

# Get and validate region
aws_region = os.getenv("AWS_REGION")


class BaseModel(Model):
    """Base model with common configurations"""

    class Meta:
        """
        Meta configuration for the DynamoDB model
        """

        region = aws_region
        read_capacity_units = 1
        write_capacity_units = 1

    id = UnicodeAttribute(hash_key=True, default=lambda: str(uuid4()))  # UUID4
    created_at = UTCDateTimeAttribute(default=datetime.now)
    updated_at = UTCDateTimeAttribute(default=datetime.now)


class Chats(BaseModel):
    """
    A DynamoDB Chat model.
    """

    class Meta(BaseModel.Meta):
        """
        Meta configuration for the Chat models
        """

        table_name = "chats"

    participants = UnicodeAttribute()


class Message(BaseModel):
    """
    A DynamoDB Message model.
    """

    class Meta(BaseModel.Meta):
        """
        Meta configuration for the MessageModel
        """

        table_name = "messages"

    chat_id = UnicodeAttribute(range_key=True)  # UUID4
    sender_id = UnicodeAttribute()  # User ID of the sender
    content = UnicodeAttribute()  # Message content
    attachments = ListAttribute(of=MapAttribute, null=True)
    is_read = BooleanAttribute(default=False)  # Track if the message is read

    def to_dict(self, user_id):
        """
        Convert model instance to dictionary
        """
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "attachments": self.attachments,
            "is_read": self.is_read,
            "is_sender": True if self.sender_id == user_id else False,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
