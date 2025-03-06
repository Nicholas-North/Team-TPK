# Import MonteCarloSimulation
from MCDynamic import MonteCarloSimulation  # Adjust import based on actual file name
from Classes import fetch_characters
import time
import random
import pyodbc

# Database connection details
DB_SERVER = 'database-1.c16m0yos4c9g.us-east-2.rds.amazonaws.com,1433'
DB_NAME = 'teamTPK'
DB_USER = 'admin'
DB_PASSWORD = 'teamtpk4vr!'

# Simulator function using MonteCarloSimulation
def run_simulator(batch_id, encounter_id, players):
    print(f"Running Monte Carlo Simulation for BatchID: {batch_id}, EncounterID: {encounter_id}")

    try:
        if not players:
            print(f"ERROR: No players found for EncounterID: {encounter_id}")
            return False
        
        for char in players:
            print(f"Character: {char.characterName}, Class: {char.characterClass}, FriendFoe: {char.friendFoe}")

        # Pass players directly to the simulation
        simulation = MonteCarloSimulation(num_simulations=10000, players=players)
        simulation.run_simulation()

        print(f"Simulation completed for BatchID: {batch_id}, EncounterID: {encounter_id}")
        return True  # Success
    except Exception as e:
        print(f"Error in simulation for BatchID: {batch_id}, EncounterID: {encounter_id}: {e}")
        return False  # Failure


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
            connection = get_db_connection()

            # Fetch enqueued batches
            enqueued_batches = fetch_enqueued_batches(connection)
            if not enqueued_batches:
                print("No enqueued batches found. Sleeping for 15 seconds...")
                time.sleep(15)
                continue

            for batch in enqueued_batches:
                batch_id, encounter_id = batch

                # Fetch players for this encounter
                players = fetch_characters(encounter_id)  # Fetch players once and pass them

                # Update batch status to 'in progress'
                print(f"Processing BatchID: {batch_id}, EncounterID: {encounter_id}")
                update_batch_status(connection, batch_id, 'in progress')

                # Run the simulator with fetched players
                if run_simulator(batch_id, encounter_id, players):
                    update_batch_status(connection, batch_id, 'complete')
                    print(f"BatchID: {batch_id} marked as complete.")
                else:
                    update_batch_status(connection, batch_id, 'failed')
                    print(f"BatchID: {batch_id} failed during simulation.")

        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

        time.sleep(1)
if __name__ == "__main__":
    batch_processor()
