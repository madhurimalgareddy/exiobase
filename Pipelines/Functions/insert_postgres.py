from sqlalchemy import create_engine
import pandas as pd

def insert_postgres(table_name, df, username, password, host, port, database):
    try:
        # Create the connection engine
        engine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}')
        
        # Insert the DataFrame into the PostgreSQL table
        df.to_sql(table_name, engine, if_exists='append', index=False)

        print(f"Successfully inserted {len(df)} rows into '{table_name}'.")

    except Exception as e:
        print(f"Failed to insert data into '{table_name}'. Error: {e}")


