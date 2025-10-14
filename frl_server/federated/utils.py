import numpy as np
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json 
from .models import ClientQTable


def aggregate_qtables(run_id):
    """
    Fetch all client Q-tables for a run_id, average the values for each state-action,
    and return a dict-of-dicts JSON structure suitable for storing in GlobalQTable.
    Only aggregates keys present in clients.
    """
    client_qs = ClientQTable.objects.all()
    if not client_qs.exists():
        return None

    # Step 1: Convert each client q_table string -> dict
    client_dicts = []
    for cq in client_qs:
        q = cq.q_table
        if isinstance(q, str):
            q = json.loads(q)
        client_dicts.append(q)

    # Step 2: Collect all keys (state tuples) across clients
    all_keys = set()
    for cd in client_dicts:
        all_keys.update(cd.keys())

    # Step 3: Aggregate each key
    aggregated = {}
    for key in all_keys:
        # For each action in this state
        action_vals_list = []
        for cd in client_dicts:
            if key in cd:
                # Collect action values as floats
                vals = [float(v) for v in cd[key].values()]
                action_vals_list.append(vals)
        # Take mean across clients
        mean_vals = np.mean(np.array(action_vals_list), axis=0)
        # Build dict-of-dict format
        aggregated[key] = {str(i): float(val) for i, val in enumerate(mean_vals)}

    return aggregated



def evaluate_qtable(qtable):
    """
    Dummy evaluation function — replace with real RL evaluation.
    For now, we'll just compute average Q-value as a proxy for performance.
    """
    q = np.array(qtable)
    return float(np.mean(q))

def broadcast_to_clients(event_type, data=None):
    """
    Sends a message to all connected clients in 'clients' group.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "clients",
        {
            "type": "control.message",
            "event": event_type,
            "data": data or {},
        }
    )

# def broadcast_new_global():
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         "clients",
#         {
#             "type": "federated.message",
#             "message": {
#                 "type": "new_global_available",
#                 "data": {}
#             }
#         }
#     )


