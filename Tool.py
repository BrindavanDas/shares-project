import DatabaseUpdater
import os
import Test
from tool_ui import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QDate

selected_item = None
start_datetime = None
end_datetime = None
db_instance = DatabaseUpdater.Database()
test_instance = Test.DataFromYahoo()


def btn_start_date():
    start_date = ui.start_date.selectedDate()
    end_date = ui.end_date.selectedDate()

    # Convert QDate objects to a format like datetime
    global start_datetime, end_datetime
    start_datetime = QDate(start_date).toPyDate()
    end_datetime = QDate(end_date).toPyDate()


def btn_connect_db():
    print("Connecting to database...")
    db_instance = DatabaseUpdater.Database()
    connection_status = db_instance.db_status()
    if connection_status:
        print("Database connected.")
        ui.db_status.setStyleSheet("background-color: rgb(0, 255, 0);")
        ui.db_status.setText("Connected")
        tables = db_instance.db_tables()
        for table_name in tables:
            item = ui.list_of_tables.addItem(table_name)
    else:
        print("Failed to connect to database.")
        ui.db_status.setStyleSheet("background-color: rgb(255, 0, 0);")
        ui.db_status.setText("Disconnected")


def capture_selected_table(item):
    selected_table = item.text()
    global selected_item
    selected_item = selected_table


def source_db_open():
    print(selected_item)
    if selected_item == "shares":
        os.startfile("F:\Projects\shares\data.xlsx")
    elif selected_item == "data_feed":
        os.startfile("F:\Projects\shares\data_feed.xlsx")
    else:
        print("Table is new!! work on code")


def update_db():
    if selected_item == "shares":
        db_instance.update_database_from_excel(
            "F:\Projects\shares\data.xlsx", "code", selected_item
        )

    else:
        print("Please select shares table")


def prices_from_yahoo():
    shares = db_instance.read_from_postgres("shares")
    shares = shares["code"].to_list()
    test_instance.prices_extract(shares, start_datetime, end_datetime)
    test_instance.save_to_excel()


def upload_prices_db():
    if selected_item == "data_feed":
        db_instance.update_database_from_excel(
            "F:\Projects\shares\data_feed.xlsx", "date", selected_item
        )
    else:
        print("Please select data_feed table")


test = Test.Path()
test.path()
test_df = test.read_excel()

app = QApplication([])

# Create the main window
window = QMainWindow()

# Set up the UI from the generated module
ui = Ui_MainWindow()
ui.setupUi(window)

ui.start_date.selectionChanged.connect(btn_start_date)
ui.end_date.selectionChanged.connect(btn_start_date)
ui.connect_db.clicked.connect(btn_connect_db)
ui.list_of_tables.itemClicked.connect(capture_selected_table)
ui.open_source_db.clicked.connect(source_db_open)
ui.update_source_db.clicked.connect(update_db)
ui.extract_prices.clicked.connect(prices_from_yahoo)
ui.update_prices.clicked.connect(upload_prices_db)


# Show the window
window.show()

# Execute the application
app.exec_()


"""
df = pd.read_excel("F:\Projects\shares\config.xlsx")


try:
    db_params = df.set_index("Details")["Credentials"].to_dict()
    engine = create_engine(
        f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}/{db_params['database']}"
    )

    metadata = MetaData()
    metadata.clear()
    metadata.reflect(bind=engine)

    table_names = metadata.tables.keys()

    for table_name in table_names:
        print(table_name)

except SQLAlchemyError as e:
    print("An error occurred:", e)"""
