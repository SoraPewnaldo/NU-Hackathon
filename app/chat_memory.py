from collections import defaultdict, deque

# In-memory per-user chat history: { user_id: deque([...]) }
# Each item: {"role": "user"/"assistant", "content": "..."}
_chat_history = defaultdict(lambda: deque(maxlen=10))

# In-memory per-user pending actions: { user_id: (action, params) }
_pending_actions = {}

def get_history(user_id):
    return list(_chat_history[user_id])

def add_to_history(user_id, role, content):
    _chat_history[user_id].append({"role": role, "content": content})

def clear_history(user_id):
    _chat_history[user_id].clear()

def set_pending_action(user_id, action, params):
    _pending_actions[user_id] = (action, params)

def get_pending_action(user_id):
    return _pending_actions.get(user_id)

def clear_pending_action(user_id):
    if user_id in _pending_actions:
        del _pending_actions[user_id]