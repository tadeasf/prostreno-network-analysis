import networkx as nx
from networkx.algorithms import community
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import pandas as pd
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import matplotlib.colors as mcolors
import time
import pickle

# Connect to the database
try:
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    print("Connected to the database.")
except Exception as e:
    print("Error connecting to the database:", str(e))
    exit()

# Fetch the user-topic data
sql = """
SELECT user_id, topic_id, weight 
FROM user_topics;
"""

try:
    user_topic_df = pd.read_sql_query(sql, engine)
    print("Fetched user-topic data from the database.")
except Exception as e:
    print("Error fetching user-topic data:", str(e))
    exit()

# Create the bipartite graph
B = nx.Graph()

# Add nodes with the node attribute "bipartite"
B.add_nodes_from(user_topic_df["user_id"].astype(str), bipartite=0)
B.add_nodes_from(user_topic_df["topic_id"].astype(str), bipartite=1)


# Add edges only between nodes of opposite node sets
def add_edges(row):
    B.add_edge(str(row["user_id"]), str(row["topic_id"]), weight=row["weight"])


user_topic_df.apply(add_edges, axis=1)

# Fetch the unique user and topic IDs
unique_user_ids = user_topic_df["user_id"].astype(str).unique()
unique_topic_ids = user_topic_df["topic_id"].astype(str).unique()

# Project the bipartite graph onto user nodes
G_user = bipartite.weighted_projected_graph(B, unique_user_ids)

# Start the timer
start_time = time.time()

# Community detection on user graph
try:
    communities = list(community.greedy_modularity_communities(G_user))
    print("Performed community detection on the user graph.")
except Exception as e:
    print("Error performing community detection:", str(e))
    exit()

# Calculate the elapsed time for community detection
elapsed_time = time.time() - start_time
print("Community detection elapsed time:", elapsed_time, "seconds")

# Project the bipartite graph onto topic nodes
G_topic = bipartite.weighted_projected_graph(B, unique_topic_ids)

# Define community colors
colors = list(mcolors.CSS4_COLORS.keys())

# Visualize the graph
plt.figure(figsize=(200, 200), dpi=80)  # Increase figure size and resolution
pos = nx.spring_layout(G_topic)

# Draw nodes and labels
nx.draw_networkx_nodes(G_topic, pos, node_color="skyblue")
nx.draw_networkx_labels(G_topic, pos)

# Draw edges and assign colors based on community
try:
    edge_colors = {}
    for u, v, d in G_topic.edges(data=True):
        shared_users = set(B.neighbors(u)).intersection(B.neighbors(v))
        d["communities"] = [
            colors[i % len(colors)]
            for i, community in enumerate(communities)
            if any(user in shared_users for user in community)
        ]
        edge_colors[(u, v)] = d["communities"]

    for color in colors:
        colored_edges = [(u, v) for (u, v), d in edge_colors.items() if color in d]
        nx.draw_networkx_edges(G_topic, pos, edgelist=colored_edges, edge_color=color)

    # Save the graph
    try:
        with open("topic_graph.pickle", "wb") as f:
            pickle.dump(G_topic, f, pickle.HIGHEST_PROTOCOL)
        print("Saved the graph as pickle.")
    except Exception as e:
        print("Error saving graph as pickle:", str(e))

    # Save as GEXF for Gephi
    for u, v, d in G_topic.edges(data=True):
        d["communities"] = ", ".join(map(str, d["communities"]))

    try:
        nx.write_gexf(G_topic, "topic_graph.gexf")
        print("Saved the graph as GEXF.")
    except Exception as e:
        print("Error saving graph as GEXF:", str(e))

    # Save the image with high resolution
    try:
        plt.savefig("topic_graph.jpg", dpi=300)
        print("Saved the graph image.")
    except Exception as e:
        print("Error saving graph image:", str(e))

    print("Script execution completed.")

except Exception as e:
    print("Error during graph visualization:", str(e))
