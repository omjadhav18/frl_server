from .models import ClientQTable, GlobalQTable

def aggregate_qtables(run_id):
    client_qtables = ClientQTable.objects.filter(run_id=run_id)

    if not client_qtables.exists():
        return None

    aggregated = {}
    count = client_qtables.count()

    for entry in client_qtables:
        q = entry.q_table
        for state, actions in q.items():
            if state not in aggregated:
                aggregated[state] = {a: 0.0 for a in actions.keys()}
            for action, value in actions.items():
                aggregated[state][action] += value

    # Average values
    for state, actions in aggregated.items():
        for action in actions:
            aggregated[state][action] /= count

    global_q = GlobalQTable.objects.create(q_table=aggregated)
    return global_q
