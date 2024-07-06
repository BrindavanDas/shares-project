import pandas as pd
from sqlalchemy import create_engine, MetaData
from psycopg2 import sql


class Database:
    """databse updater for postgres"""

    def __init__(self):
        self.config = pd.read_excel(
            "F:\Projects\shares\config.xlsx", sheet_name="config"
        )
        self.db_params = self.config.set_index("Details")["Credentials"].to_dict()
        self.engine = create_engine(
            f"postgresql+psycopg2://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}/{self.db_params['database']}"
        )
        self.metadata = MetaData()

    def db_status(self):
        try:
            # Attempt to establish a connection
            with self.engine.connect():
                return True  # Connection successful
        except Exception as e:
            print(f"Connection error: {e}")
            return False  # Connection failed

    def db_tables(self):
        self.metadata.clear()
        self.metadata.reflect(bind=self.engine)
        self.table_names = self.metadata.tables.keys()
        return self.table_names

    def read_from_postgres(self, table_name):
        """read the data from database"""
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, self.engine)
        return df

    def update_postgres(self, df, table_name):
        """update the data from database"""
        df.to_sql(table_name, self.engine, if_exists="replace", index=False)

    def save_to_excel(self, df, file_path):
        """saves the database extract in excel for amendment"""
        df.to_excel(file_path, index=False)

    def read_from_excel(self, file_path):
        """read the excel version of db extract"""
        df = pd.read_excel(file_path)
        return df

    def update_database_from_excel(self, excel_file_path, column_to_match, table_name):
        """update the databse with changes made in excel file"""
        data_from_excel = self.read_from_excel(excel_file_path)
        data_from_db = self.read_from_postgres(table_name)
        if data_from_db.empty:
            self.update_postgres(data_from_excel, table_name)
            print("Data updated in the database.")
            return
        new_rows = data_from_excel[
            ~data_from_excel[column_to_match].isin(data_from_db[column_to_match])
        ]
        existing_rows = data_from_excel[
            data_from_excel[column_to_match].isin(data_from_db[column_to_match])
        ]
        updated_data = pd.concat([data_from_db, new_rows], ignore_index=True)
        self.update_postgres(updated_data, table_name)
        print("Data updated in the database.")
