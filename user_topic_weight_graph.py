import networkx as nx
from networkx.algorithms import community
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import pandas as pd
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import matplotlib.colors as mcolors

# Connect to the database
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# Fetch the user-topic data
sql = """
SELECT user_id, topic_id, weight 
FROM user_topics;
"""
user_topic_df = pd.read_sql_query(sql, engine)

# Create the bipartite graph
B = nx.Graph()

# Add nodes with the node attribute "bipartite"
B.add_nodes_from(user_topic_df["user_id"].astype(str), bipartite=0)
B.add_nodes_from(user_topic_df["topic_id"].astype(str), bipartite=1)

# Add edges only between nodes of opposite node sets
B.add_weighted_edges_from(
    [
        (str(row["user_id"]), str(row["topic_id"]), row["weight"])
        for idx, row in user_topic_df.iterrows()
    ]
)

# Fetch the unique user and topic IDs
unique_user_ids = user_topic_df["user_id"].astype(str).unique()
unique_topic_ids = user_topic_df["topic_id"].astype(str).unique()

# Project the bipartite graph onto user nodes
G_user = bipartite.weighted_projected_graph(B, unique_user_ids)

# Community detection on user graph
communities = list(community.greedy_modularity_communities(G_user))

# Project the bipartite graph onto topic nodes
G_topic = bipartite.weighted_projected_graph(B, unique_topic_ids)

# Define community colors
colors = list(mcolors.CSS4_COLORS.keys())

# Visualize the graph
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G_topic)

# Draw nodes
nx.draw_networkx_nodes(G_topic, pos, node_color="skyblue")

# Draw edges and assign colors based on community
for u, v, d in G_topic.edges(data=True):
    shared_users = set(B.neighbors(u)).intersection(B.neighbors(v))
    d["communities"] = [
        colors[i % len(colors)]
        for i, community in enumerate(communities)
        if any(user in shared_users for user in community)
    ]
    edge_colors = d["communities"]
    for color in edge_colors:
        nx.draw_networkx_edges(G_topic, pos, edgelist=[(u, v)], edge_color=color)

# Save the graph
nx.write_gpickle(G_topic, "topic_graph.gpickle")

# Save as GEXF for Gephi
nx.write_gexf(G_topic, "topic_graph.gexf")

# Save the image
plt.savefig("topic_graph.jpg")

# Show the plot
plt.show()
