from sqlalchemy.orm import sessionmaker
import networkx as nx
from sqlalchemy import create_engine
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from models import User, Topic, Follower, UserTopic
import ndex2  # Import NDEx client
import json

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)


def build_graph(session):
    G = nx.Graph()

    # Add nodes for users and topics
    for user in session.query(User).all():
        followers = session.query(Follower).filter(Follower.user_id == user.id).count()
        G.add_node(
            user.id,
            size=followers,
            label=user.username,
            viz={"color": {"r": 255, "g": 0, "b": 0, "a": 0}},
        )

    for topic in session.query(Topic).all():
        users = session.query(UserTopic).filter(UserTopic.topic_id == topic.id).count()
        G.add_node(
            topic.id,
            size=users,
            label=topic.topic,
            viz={"color": {"r": 0, "g": 255, "b": 0, "a": 0}},
        )

    # Add edges for user-topic relationships
    for user_topic in session.query(UserTopic).all():
        user = session.query(User).filter(User.id == user_topic.user_id).one()
        topic = session.query(Topic).filter(Topic.id == user_topic.topic_id).one()
        G.add_edge(user.id, topic.id, weight=user_topic.weight)

    return G


if __name__ == "__main__":
    session = Session()
    G = build_graph(session)

    # Convert NetworkX graph to NDEx format
    nice_cx_network = ndex2.create_nice_cx_from_networkx(G)

    # Save NDEx format to a file
    nice_cx_network.print_summary()
    with open("twitter_data.json", "w") as outfile:
        json.dump(nice_cx_network.to_cx(), outfile)
