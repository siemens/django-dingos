# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

create_build_graph = """-- Function build_graph(int[], direction text, depth int, max_nodes int)
-- returns a serialized graph object

CREATE FUNCTION build_graph_table(pkslist int[], direction text, depth int, max_nodes int)
RETURNS text
AS $$
from dingos.core.db_graphtools import build_graph_table
return build_graph_table(pkslist, direction, depth, max_nodes, plpy)
$$ LANGUAGE plpythonu"""

remove_build_graph = """DROP FUNCTION build_graph_table(int[], text, int, int)"""


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0005_add_stored_function'),
    ]

    operations = [
        migrations.RunSQL(
            create_build_graph,
            remove_build_graph
        ),
    ]
