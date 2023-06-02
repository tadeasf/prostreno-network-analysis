from sqlalchemy import create_engine, MetaData
from neo4j import GraphDatabase
from config import (
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
)


def extract_data_from_postgresql():
    pg_db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(pg_db_url)
    connection = engine.connect()

    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Get a list of all tables in the database
    tables = metadata.sorted_tables

    # Extract data from each table
    data = {}
    for table in tables:
        query = table.select()
        result = connection.execute(query)
        rows = result.fetchall()
        data[table.name] = {"rows": rows, "columns": table.c}

    connection.close()
    return data


def import_data_to_neo4j(data):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Check if the Neo4j database is empty
        result = session.run("MATCH (n) RETURN count(n) AS count")
        count = result.single()["count"]
        if count > 0:
            # Remove existing data from the Neo4j database
            session.run("MATCH (n) DETACH DELETE n")

        # Create nodes for users, tweets, topics, followers, and following
        for table_name in ["users", "tweets", "topics", "followers", "following"]:
            for row in data[table_name]["rows"]:
                row_dict = row._asdict()
                properties = {
                    column.name: row_dict[column.name]
                    for column in data[table_name]["columns"]
                    if row_dict[column.name] is not None
                    and row_dict[column.name] != "NO_VALUE"
                    and not isinstance(row_dict[column.name], dict)
                }
                session.run(f"CREATE (:{table_name} $props)", props=properties)

        # Create relationships between users and tweets
        for row in data["tweets"]["rows"]:
            row_dict = row._asdict()
            session.run(
                "MATCH (u:users), (t:tweets) "
                "WHERE u.id = $author_id AND t.id = $tweet_id "
                "CREATE (u)-[:AUTHORED]->(t)",
                author_id=row_dict["author_id"],
                tweet_id=row_dict["id"],
            )

        # Create relationships between tweets and topics
        for row in data["tweet_topics"]["rows"]:
            row_dict = row._asdict()
            session.run(
                "MATCH (t:tweets), (topic:topics) "
                "WHERE t.id = $tweet_id AND topic.id = $topic_id "
                "CREATE (t)-[:HAS_TOPIC]->(topic)",
                tweet_id=row_dict["tweet_id"],
                topic_id=row_dict["topic_id"],
            )

        # Create relationships between users and topics with weights
        for row in data["user_topics"]["rows"]:
            row_dict = row._asdict()
            session.run(
                "MATCH (u:users), (topic:topics) "
                "WHERE u.id = $user_id AND topic.id = $topic_id "
                "CREATE (u)-[:INTERESTED_IN {weight: $weight}]->(topic)",
                user_id=row_dict["user_id"],
                topic_id=row_dict["topic_id"],
                weight=row_dict["weight"],
            )

        # Create relationships between users for followers and following
        for row in data["followers"]["rows"]:
            row_dict = row._asdict()
            session.run(
                "MATCH (u1:users), (u2:users) "
                "WHERE u1.id = $user_id AND u2.id = $follower_id "
                "CREATE (u1)-[:FOLLOWS]->(u2)",
                user_id=row_dict["user_id"],
                follower_id=row_dict["follower_id"],
            )

        for row in data["following"]["rows"]:
            row_dict = row._asdict()
            session.run(
                "MATCH (u1:users), (u2:users) "
                "WHERE u1.id = $user_id AND u2.id = $following_id "
                "CREATE (u1)-[:FOLLOWS]->(u2)",
                user_id=row_dict["user_id"],
                following_id=row_dict["following_id"],
            )

        # Add sentiment_analysis as a property to the HAS_TOPIC relationship
        for row in data["tweets"]["rows"]:
            row_dict = row._asdict()
            if row_dict["sentiment_analysis"]:
                session.run(
                    "MATCH (t:tweets)-[r:HAS_TOPIC]->(topic:topics) "
                    "WHERE t.id = $tweet_id "
                    "SET r.sentiment_analysis = $sentiment_analysis",
                    tweet_id=row_dict["id"],
                    sentiment_analysis=row_dict["sentiment_analysis"],
                )

    driver.close()


def main():
    data = extract_data_from_postgresql()
    import_data_to_neo4j(data)
    print("Data imported successfully into Neo4j!")


if __name__ == "__main__":
    main()
