# How to alembic

The issue here is that SQLAlchemy's create_all method doesn't alter existing tables, it only creates new ones. If you want to add new columns to an existing table, you'll need to use a database migration tool. One such tool is Alembic, which is designed to work with SQLAlchemy.

Here's a brief guide on how you can use Alembic to add new columns to your existing table:

    Install Alembic using pip:

bash

pip install alembic

    Initialize Alembic in your project directory:

bash

alembic init alembic

This will create a new directory named alembic in your project directory, along with a alembic.ini file.

    Configure the alembic.ini file to use your database URL. You'll find a line that starts with sqlalchemy.url in the alembic.ini file. Replace its value with your database URL.

    In the alembic directory, open the env.py file and change the target_metadata variable to point to your SQLAlchemy Base metadata:

python

from models import Base
target_metadata = Base.metadata

    Now you can generate a migration script:

bash

alembic revision --autogenerate -m "Added sentiment_analysis and topic columns"

This will create a new Python script in the alembic/versions directory.

    Open the generated script in alembic/versions. You should see two functions: upgrade() and downgrade(). In the upgrade() function, Alembic should have automatically added lines of code to add the new columns to your tweets table. In the downgrade() function, it should have added lines of code to remove these columns.

    If everything looks correct, you can apply the migration with:

bash

alembic upgrade head

This will run the upgrade() function in your migration script, which should add the new columns to your tweets table.

Remember, always backup your database before running migrations on it, especially when you're new to using a tool like Alembic.