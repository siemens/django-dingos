-- Function build_graph(int[], string)
-- returns a serialized graph object

CREATE FUNCTION build_graph(pkslist int[], direction text, depth int)
RETURNS text
AS $$
from dingos.core.db_graphtools import build_graph
return build_graph(pkslist, direction, depth, plpy)
$$ LANGUAGE plpythonu