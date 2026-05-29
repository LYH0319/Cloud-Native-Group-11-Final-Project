def has_cycle(job_id, dependencies, visited=None, stack=None):
    # initialize tracking set
    if visited is None:
        visited = set()
    if stack is None:
        stack = set()

    # mark current node
    visited.add(job_id)
    stack.add(job_id)

    # DFS check neighbors recursively
    for neighbor in dependencies.get(job_id, []):
        if neighbor not in visited:
            if has_cycle(neighbor, dependencies, visited, stack):
                return True
        elif neighbor in stack:
            return True

    # leave and remove the node
    stack.remove(job_id)
    return False
