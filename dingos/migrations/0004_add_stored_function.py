# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


create_build_graph = """-- Function build_graph(int[], string)
-- returns a serialized graph object

CREATE FUNCTION build_graph(pkslist int[], direction text, depth int, max_nodes int)
RETURNS text
AS $$
from dingos.core.db_graphtools import build_graph
return build_graph(pkslist, direction, depth, max_nodes, plpy)
$$ LANGUAGE plpythonu"""

remove_build_graph = """DROP FUNCTION build_graph(int[], text, int, int)"""

class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0001_initial'),
        ('dingos', '0002_add_vIO2FValue_view'),
        ('dingos', '0003_vio2fvalue'),
    ]

    operations = [
        migrations.RunSQL(
            create_build_graph,
            remove_build_graph
        ),
    ]
