from app.critical_info import process_unprocessed_conversations
from app.db import init_db
from app.decision_records import sync_missing_decision_records


if __name__ == "__main__":
    init_db()
    conversations_result = process_unprocessed_conversations()
    decisions_result = sync_missing_decision_records()
    print(
        {
            "conversations": conversations_result,
            "missing_decision_records": decisions_result,
        }
    )
