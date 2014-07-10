
def dfs_preorder_nodes(G, source=None,edge_pred=None):
    """Produce nodes in a depth-first-search pre-ordering starting
    from source.

    Parameters
    ----------
    G : NetworkX graph

    source : node, optional
       Specify starting node for depth-first search and return edges in
       the component reachable from source.

    Returns
    -------
    nodes: generator
       A generator of nodes in a depth-first-search pre-ordering.

    Examples
    --------
    >>> G = nx.Graph()
    >>> G.add_path([0,1,2])
    >>> print(list(nx.dfs_preorder_nodes(G,0)))
    [0, 1, 2]

    Notes
    -----
    Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    by D. Eppstein, July 2004.

    If a source is not specified then a source is chosen arbitrarily and
    repeatedly until all components in the graph are searched.
    """
    pre=(v for u,v,d in dfs_labeled_edges(G,source=source,edge_pred=edge_pred)
         if d['dir']=='forward')
    # potential modification: chain source to beginning of pre-ordering
    # return chain([source],pre)
    return pre

def dfs_labeled_edges(G, source=None,edge_pred=None):
    """Produce edges in a depth-first-search (DFS) labeled by type.

    Parameters
    ----------
    G : NetworkX graph

    source : node, optional
       Specify starting node for depth-first search and return edges in
       the component reachable from source.

    Returns
    -------
    edges: generator
       A generator of edges in the depth-first-search labeled with 'forward',
       'nontree', and 'reverse'.

    Examples
    --------
    >>> G = nx.Graph()
    >>> G.add_path([0,1,2])
    >>> edges = (list(nx.dfs_labeled_edges(G,0)))

    Notes
    -----
    Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    by D. Eppstein, July 2004.

    If a source is not specified then a source is chosen arbitrarily and
    repeatedly until all components in the graph are searched.
    """
    # Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    # by D. Eppstein, July 2004.

    def adj_filter(G,node,edge_pred):
        if not edge_pred:
            return iter(G[node])
        adjacent_nodes = G.adj[node]
        result = []
        for n in adjacent_nodes.keys():
            print adjacent_nodes[n].values()
            valid_edges = [e for e in adjacent_nodes[n].values() if edge_pred(e)]
            if valid_edges:
                result.append(n)
        return iter(result)

    if source is None:
        # produce edges for all components
        nodes = G
    else:
        # produce edges for components with source
        nodes = [source]
    visited = set()
    for start in nodes:
        if start in visited:
            continue
        yield start,start,{'dir':'forward'}
        visited.add(start)
        adj_nodes = adj_filter(G,start,edge_pred)
        stack = [(start,adj_nodes)]
        while stack:
            parent,children = stack[-1]
            try:
                child = next(children)
                if child in visited:
                    yield parent,child,{'dir':'nontree'}
                else:
                    yield parent,child,{'dir':'forward'}
                    visited.add(child)
                    adj_nodes = adj_filter(G,child,edge_pred)
                    stack.append((child,adj_nodes))
            except StopIteration:
                stack.pop()
                if stack:
                    yield stack[-1][0],parent,{'dir':'reverse'}
        yield start,start,{'dir':'reverse'}
