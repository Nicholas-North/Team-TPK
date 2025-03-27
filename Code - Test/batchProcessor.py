from concurrent.futures import ProcessPoolExecutor, as_completed
from MCDynamic import MonteCarloSimulation  # Adjust import based on actual file name
from Classes import fetch_characters
import time
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
            return False, None, None
        
        for char in players:
            print(f"Character: {char.characterName}, Class: {char.characterClass}, FriendFoe: {char.friendFoe}")

        # Pass players directly to the simulation
        simulation = MonteCarloSimulation(num_simulations=10000, players=players, encounter_id=encounter_id)
        simulation.run_simulation()
        team1_wins, team2_wins = simulation.display_results()

        print("\nFinal Results:")
        print(f"Friends: {team1_wins} wins")
        print(f"Foes: {team2_wins} wins")

        print(f"Simulation completed for BatchID: {batch_id}, EncounterID: {encounter_id}")
        return True, team1_wins / 100, team2_wins / 100  # Success
    
    except Exception as e:
        print(f"Error in simulation for BatchID: {batch_id}, EncounterID: {encounter_id}: {e}")
        return False, None, None  # Failure

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

def get_account_id(connection, encounter_id):
    cursor = connection.cursor()
    query = """
        SELECT accountID
        FROM encounter.encounter
        WHERE encounterID = ?
    """
    cursor.execute(query, (encounter_id,))
    row = cursor.fetchone()
    return row[0] if row else None

# Function to insert into encounterHistory
def update_encounter_history(connection, batch_id, encounter_id, account_id, team1_wins, team2_wins):
    cursor = connection.cursor()
    query = """
        INSERT INTO encounter.encounterHistory (batchID, encounterID, accountID, team1Wins, team2Wins)
        VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(query, (batch_id, encounter_id, account_id, team1_wins, team2_wins))
    connection.commit()

# Function to process a single batch
def process_batch(batch):
    batch_id, encounter_id = batch
    connection = get_db_connection()

    try:
        # Fetch players for this encounter
        players = fetch_characters(encounter_id)  # Fetch players once and pass them

        # Update batch status to 'in progress'
        print(f"Processing BatchID: {batch_id}, EncounterID: {encounter_id}")
        update_batch_status(connection, batch_id, 'in progress')

        # Run the simulator with fetched players
        simulator_results, team1_wins, team2_wins = run_simulator(batch_id, encounter_id, players)
        
        if simulator_results:
            update_batch_status(connection, batch_id, 'complete')
            print(f"BatchID: {batch_id} marked as complete.")
        else:
            update_batch_status(connection, batch_id, 'failed')
            print(f"BatchID: {batch_id} failed during simulation.")

        # Get accountID associated with the encounterID
        account_id = get_account_id(connection, encounter_id)
        if not account_id:
            print(f"Error: No accountID found for EncounterID: {encounter_id}")
            update_batch_status(connection, batch_id, 'failed')
            return

        # Update encounterHistory with simulation results
        update_encounter_history(connection, batch_id, encounter_id, account_id, team1_wins, team2_wins)

    except Exception as e:
        print(f"Error processing BatchID: {batch_id}: {e}")
        update_batch_status(connection, batch_id, 'failed')
    finally:
        connection.close()

# Main batch processor function
def batch_processor():
    print("Batch Processor started. Waiting for enqueued batches...")
    while True:
        try:
            connection = get_db_connection()

            # Fetch enqueued batches
            enqueued_batches = fetch_enqueued_batches(connection)
            if not enqueued_batches:
                print("No enqueued batches found. Sleeping for 5 seconds...")
                time.sleep(5)
                continue

            # Use ProcessPoolExecutor to process batches in parallel
            with ProcessPoolExecutor() as executor:
                futures = {executor.submit(process_batch, batch): batch for batch in enqueued_batches}
                for future in as_completed(futures):
                    batch = futures[future]
                    try:
                        future.result()  # Ensure the process completed successfully
                    except Exception as e:
                        print(f"Error processing batch {batch}: {e}")

        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            if 'connection' in locals():
                connection.close()

        time.sleep(1)

if __name__ == "__main__":
    batch_processor()