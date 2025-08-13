from pyspark.sql import DataFrame

def insert_postgres_spark(df: DataFrame, table_name: str, username: str, password: str, host: str, port: int, database: str):
    try:
        # JDBC URL format for PostgreSQL
        jdbc_url = f"jdbc:postgresql://{host}:{port}/{database}"
        
        # Connection properties
        connection_properties = {
            "user": username,
            "password": password,
            "driver": "org.postgresql.Driver"
        }

        # Write DataFrame to PostgreSQL table
        df.write.jdbc(url=jdbc_url, table=table_name, mode="append", properties=connection_properties)
        
        print(f"Successfully inserted {df.count()} rows into '{table_name}'.")

    except Exception as e:
        print(f"Failed to insert data into '{table_name}'. Error: {e}")
