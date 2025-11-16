from collections import defaultdict, deque

# In-memory per-user chat history: { user_id: deque([...]) }
# Each item: {"role": "user"/"assistant", "content": "..."}
_chat_history = defaultdict(lambda: deque(maxlen=10))

def get_history(user_id):
    return list(_chat_history[user_id])

def add_to_history(user_id, role, content):
    _chat_history[user_id].append({"role": role, "content": content})

def clear_history(user_id):
    _chat_history[user_id].clear()