from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
from supports.middleware import jwt_middleware
from models import Chats, Message
from serializers import MessageSerializer
import pusher

app = FastAPI()
app.middleware("http")(jwt_middleware)

# Load .env file
load_dotenv()

pusher_client = pusher.Pusher(
    app_id=os.getenv("PUSHER_APP_ID"),
    key=os.getenv("PUSHER_KEY"),
    secret=os.getenv("PUSHER_SECRET"),
    cluster=os.getenv("PUSHER_CLUSTER"),
    ssl=os.getenv("PUSHER_SSL") == "True",
)


@app.get("/")
async def protected_endpoint(request: Request):
    user = request.state.user
    return {
        "message": "Access granted",
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "full_payload": user,
    }


@app.get("/chats/{user1}/{user2}")
async def get_or_create_chat(user1: str, user2: str):
    """
    Get or create a chat between two users.
    """
    try:
        # Sort user IDs to ensure consistent order for chat participants
        participants_str = ",".join(sorted([user1, user2]))

        # Search for an existing chat
        existing_chats = list(Chats.scan(Chats.participants.contains(participants_str)))

        # If a chat exists, return it
        if existing_chats:
            chat = existing_chats[0]
            return {
                "id": chat.id,
                "participants": chat.participants.split(","),
                "created_at": chat.created_at.isoformat(),
                "updated_at": chat.updated_at.isoformat(),
            }

        # If no chat exists, create a new one
        new_chat = Chats(participants=participants_str)
        new_chat.save()

        return {
            "id": new_chat.id,
            "participants": new_chat.participants.split(","),
            "created_at": new_chat.created_at.isoformat(),
            "updated_at": new_chat.updated_at.isoformat(),
        }

    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(err)}",
        )


@app.post("/chats/{chat_id}/send-message")
async def send_message(chat_id: str, message: MessageSerializer, request: Request):
    """
    Send a message to a chat.
    """
    user = request.state.user
    user_id = user.get("user_id")
    message_data = message.model_dump(exclude_unset=True)
    message_data["chat_id"] = str(chat_id)
    message_data["sender_id"] = user_id

    try:
        new_message = Message(**message_data)
        new_message.save()
        data = {
            "id": new_message.id,
            "chat_id": new_message.chat_id,
            "sender_id": new_message.sender_id,
            "content": new_message.content,
            "attachments": new_message.attachments,
            "is_read": new_message.is_read,
            "is_sender": True if new_message.sender_id == user_id else False,
            "created_at": (
                new_message.created_at.isoformat() if new_message.created_at else None
            ),
            "updated_at": (
                new_message.updated_at.isoformat() if new_message.updated_at else None
            ),
        }
        # send the message to pusher
        pusher_client.trigger(chat_id, user_id, {"message": data})
        return {
            "message": "Success",
            "data": data,
            "success": True,
        }
    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Error sending message: {str(err)}"
        )


@app.get("/messages/{chat_id}")
async def get_messages(chat_id: str, request: Request):
    """
    Retrieve messages for a specific chat.
    """
    user = request.state.user

    try:
        # Correct the scan method usage
        messages = list(Message.scan(Message.chat_id == chat_id))

        # Convert messages to a list of dictionaries
        messages_data = [message.to_dict(user.get("user_id")) for message in messages]

        return {"message": "Success", "data": messages_data, "success": True}
    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving messages: {str(err)}"
        )


@app.get("/messages/{chat_id}/{message_id}")
async def get_message(message_id: str, chat_id: str, request: Request):
    """
    Retrieve a single message by its ID and chat ID.
    """
    user = request.state.user
    try:
        # Retrieve the specific message using both hash and range keys
        message = Message.get(hash_key=message_id, range_key=chat_id)

        return {
            "message": "Success",
            "data": message.to_dict(user.get("user_id")),
            "success": True,
        }
    except Message.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail=f"Message with ID {message_id} not found in chat {chat_id}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving message: {str(err)}"
        )
