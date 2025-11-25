from backend.app import create_app
from backend.extensions import db
from sqlalchemy_schemadisplay import create_schema_graph

app = create_app()

with app.app_context():
    graph = create_schema_graph(metadata=db.metadata, engine=db.engine, show_datatypes=False, show_indexes=False, rankdir="TB")
    if hasattr(graph, "graph_attr"):
        graph.graph_attr.update({"splines": "ortho", "overlap": "false"})
    if hasattr(graph, "node_attr"):
        graph.node_attr.update({"shape": "record", "style": "filled", "fillcolor": "#f6f8fa"})
    graph.write_png("db-schema.png")
