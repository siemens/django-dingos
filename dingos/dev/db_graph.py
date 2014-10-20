class Node():
  def __init__(self, id, attr_dic=None):
    self.id = id
    self.attr_dic = attr_dic

  def update(self, attr_dic_new):
    if self.attr_dic:
        self.attr_dic.update(attr_dic_new)
    else:
        self.attr_dic = attr_dic_new


class Edge():
  def __init__(self, start, end, attr_dic=None):
    self.start = start
    self.end = end
    self.attr_dic = attr_dic

  def update(self, attr_dic_new):
    if self.attr_dic:
        self.attr_dic.update(attr_dic_new)
    else:
        self.attr_dic = attr_dic_new


class Graph_DB():
  def __init__(self):
    self.nodes = {}
    self.edges = {}

  def add_node(self,id, node_attr_dic=None):
    if id in self.nodes:
      self.nodes[id].update(node_attr_dic)
    else:
      self.nodes[id] = Node(id, node_attr_dic)

  def add_edge(self, start, end, edge_attr_dic=None):
    if (start,end) in self.edges:
      self.edges[(start,end)].update(edge_attr_dic)

    else:
      self.edges[(start,end)] = Edge(start, end, edge_attr_dic)