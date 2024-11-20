from botocore.exceptions import ClientError
from pynamodb.exceptions import TableError
from models import Chats, Message


def create_tables():
    """Create the DynamoDB table for products"""
    try:
        for model in [Chats, Message]:
            if not model.exists():
                try:
                    model.create_table(wait=True)
                    print(f"Table {model} created successfully")
                except ClientError as ce:
                    print(f"AWS Client Error: {ce.response['Error']['Message']}")
                    return False
                except TableError as te:
                    print(f"Table Error: {str(te)}")
                    return False
            else:
                print(f"Table {model} already exists")
                return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    create_tables()
