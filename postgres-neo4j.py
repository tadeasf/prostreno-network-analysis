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
        # Create nodes for users and tweets
        for table_name in ["users", "tweets"]:
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

        # Create relationships between users based on following and followers tables
        for table_name in ["following", "followers"]:
            for row in data[table_name]["rows"]:
                row_dict = row._asdict()
                session.run(
                    "MATCH (u1:users), (u2:users) "
                    "WHERE u1.id = $id1 AND u2.id = $id2 "
                    f"CREATE (u1)-[:{table_name.upper()}]->(u2)",
                    id1=row_dict["user_id"],
                    id2=row_dict["follower_id"]
                    if table_name == "followers"
                    else row_dict["following_id"],
                )

    driver.close()


def main():
    data = extract_data_from_postgresql()
    import_data_to_neo4j(data)
    print("Data imported successfully into Neo4j!")


if __name__ == "__main__":
    main()
