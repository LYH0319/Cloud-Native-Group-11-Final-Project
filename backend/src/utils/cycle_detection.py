from typing import Dict, List


def has_cycle(
    job_id: int, dependencies_graph: Dict[int, List[int]], visited=None, stack=None
) -> bool:
    """
    使用 DFS 偵測 DAG（有向無環圖）是否成環。
    dependencies_graph 結構範例: { 2: [1], 3: [1, 2] } 代表 2 依賴 1，3 依賴 1 和 2。
    """
    # initialize tracking set
    if visited is None:
        visited = set()
    if stack is None:
        stack = set()

    # mark current node
    visited.add(job_id)
    stack.add(job_id)

    # DFS check neighbors recursively
    for neighbor in dependencies_graph.get(job_id, []):
        if neighbor not in visited:
            if has_cycle(neighbor, dependencies_graph, visited, stack):
                return True
        elif neighbor in stack:
            return True  # 繞回目前路徑上的節點，偵測到環！

    # leave and remove the node
    stack.remove(job_id)
    return False
