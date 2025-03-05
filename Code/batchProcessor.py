import time
import random
import pyodbc

# Database connection details
DB_SERVER = 'database-1.c16m0yos4c9g.us-east-2.rds.amazonaws.com,1433'
DB_NAME = 'teamTPK'
DB_USER = 'admin'
DB_PASSWORD = 'teamtpk4vr!'

# Simulator function (mock implementation)
def run_simulator(batch_id, encounter_id):
    print(f"Running simulator for BatchID: {batch_id}, EncounterID: {encounter_id}")
    time.sleep(random.randint(1, 5))  # Simulate processing time
    print(f"Simulator completed for BatchID: {batch_id}, EncounterID: {encounter_id}")
    return True  # Simulate success

# Database connection function
def get_db_connection():
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"
    return pyodbc.connect(connection_string)

# Function to fetch enqueued batches
def fetch_enqueued_batches(connection):

    cursor = connection.cursor()
    query = """
        SELECT batchID, encounterID
        FROM batch.batch
        WHERE batchStatus = 'enqueued'
    """
    cursor.execute(query)
    return cursor.fetchall()

# Function to update batch status
def update_batch_status(connection, batch_id, status):
    cursor = connection.cursor()
    if status == 'complete':
        query = """
            UPDATE batch.batch
            SET batchStatus = ?, endTime = GETDATE()
            WHERE batchID = ?
        """
    else:
        # Update only the status
        query = """
            UPDATE batch.batch
            SET batchStatus = ?
            WHERE batchID = ?
        """
    cursor.execute(query, (status, batch_id))
    connection.commit()

# Main batch processor function
def batch_processor():
    print("Batch Processor started. Waiting for enqueued batches...")
    while True:
        try:
            # Connect to the database
            connection = get_db_connection()

            # Fetch enqueued batches
            enqueued_batches = fetch_enqueued_batches(connection)
            if not enqueued_batches:
                print("No enqueued batches found. Sleeping for 15 seconds...")
                time.sleep(15) 
                continue

            # Process each enqueued batch
            for batch in enqueued_batches:
                batch_id, encounter_id = batch

                # Update batch status to 'in progress'
                print(f"Processing BatchID: {batch_id}, EncounterID: {encounter_id}")
                update_batch_status(connection, batch_id, 'in progress')

                # Run the simulator
                if run_simulator(batch_id, encounter_id):
                    # Update batch status to 'complete' on success
                    update_batch_status(connection, batch_id, 'complete')
                    print(f"BatchID: {batch_id} marked as complete.")
                else:
                    # Handle failure (e.g., update status to 'failed')
                    update_batch_status(connection, batch_id, 'failed')
                    print(f"BatchID: {batch_id} failed during simulation.")

        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            # Close the database connection
            if 'connection' in locals():
                connection.close()

        # Sleep for a short time before checking again
        time.sleep(1)

if __name__ == "__main__":
    batch_processor()