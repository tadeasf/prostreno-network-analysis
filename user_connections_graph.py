import networkx as nx
from networkx.algorithms import community
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import pandas as pd
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Connect to the database
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# Fetch the user-follower data
sql = """
SELECT user_id, follower_id 
FROM followers;
"""
follower_df = pd.read_sql_query(sql, engine)

# Fetch the user-following data
sql = """
SELECT user_id, following_id 
FROM following;
"""
following_df = pd.read_sql_query(sql, engine)

# Combine the data
connections_df = pd.concat(
    [follower_df.rename(columns={"follower_id": "following_id"}), following_df]
)

# Create the bipartite graph
B = nx.Graph()
# Add nodes with the node attribute "bipartite"
B.add_nodes_from(connections_df["user_id"], bipartite=0)
B.add_nodes_from(connections_df["following_id"], bipartite=1)
# Add edges only between nodes of opposite node sets
B.add_edges_from(
    [(row["user_id"], row["following_id"]) for idx, row in connections_df.iterrows()]
)

# Project the bipartite graph onto user nodes
G = bipartite.projected_graph(B, connections_df["user_id"])

# Community detection
communities = list(community.greedy_modularity_communities(G))

# Print communities
for i, com in enumerate(communities):
    print(f"Community {i+1}: {list(com)}")

# Find and print influential nodes
centrality = nx.degree_centrality(G)
influential_nodes = sorted(centrality, key=centrality.get, reverse=True)[:10]
print(f"Most influential nodes: {influential_nodes}")

# Find shortest paths between communities
paths = []
for i in range(len(communities) - 1):
    for j in range(i + 1, len(communities)):
        paths.append(nx.shortest_path(G, communities[i], communities[j]))

# Print paths
for path in paths:
    print(f"Path: {path}")

# Visualize the graph
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G)
nx.draw_networkx_edges(G, pos)
nx.draw_networkx_labels(G, pos)
nx.draw_networkx_nodes(G, pos, node_size=[v * 5000 for v in centrality.values()])
plt.savefig("user_connection_graph.jpg")

# Save the graph
nx.write_gpickle(G, "user_connection_graph.gpickle")
