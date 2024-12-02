# Architecture Overview

## Front-End Webapp

The front-end web application will be the way our user's interact with our product, and is how we get input into our database, and show the output of the simulations. To do this, we have the following main capabilities that the application must be able to accomplish:

1. User Authentication
    - Users must be able to create an account
    - Users must be able to log in to an account
2. Combat Encounter Creation
    - Users need to have a way to create character(s) and monster(s) that replicate their encounter they wish to test
    - Users should be able to easily mimic character and NPC behavior through the modification/adding of production rules
    - Users should be able to edit these values after runs: meaning that if a user has an account, they'll be able to choose from previously created encounters
    - All of this encounter information should be able to be uploaded to the database
3. Combat Encounter Simulation
    - Users should be able to see the outcome of their encounter simulations
    - Users should be able to delve into combat specifics: average turn time, amount of players vanquished, percent chance of total party kill, etc.
    - If possible, Users should be able to see visualizations of the data, rather than just basic spreadsheets.

## Back-End Database

The database is how we will maintain user data, feed the various inputs of our model creation, and record the results of those encounters. We've decided to go with SQL Server Management Studio (SSMS) as our main SQL editor and SQL server. This database will need to accomplish the following:

- Be able to form two-way connections with the web application
- Have a connection be made to the remote server that our simulation will be running on
- Have database's set up for user information, encounter information, simulation runs, logging

## Character Model / Simulation

Our ability to simulate these combat encounter's is the crux of our project, and after heavy discussion's with our advisor we've come up with the following implementation plan. We will be using a production ruleset to mimic character behavior, having one large state vector that is the same for every possible model, and then having our differentiations between the models be based off which templates we give them. Below gives a rough breakdown of how we expect the information to be translated into a state vector and used in the model.

1. Translate the character values
    - Convert the statistics used to build a character sheet, i.e Health, AC, movement, into binary or float values from 0-1 and assign them to a field in the state vector
    - Do this for all characters, PC & NPC alike
    - Upload any production rules not included in the default set to each character
    - Begin the second phase with all state vectors initialized
2. Begin the round of combat
    - Based off of a value called initiative order, have each each character go based once in descending order and run their state vector across their loaded templates
    - Choose the matching templates, or use an algorithm to determine which template to use in a case of multiple matches, and conduct the action associated with that template
    - Determine the affects of that action, and update every characters state vector accordingly, before moving onto the next character
    - Repeate until the last character has gone. Then, repeat the round until certain encounter conditions are met (example: all enemies defeated or routed)
3. Run a monte carlo simulation
    - This simulation will re-run step two a pre-determined amount of times, allowing for the randomization of dice rolls to be shown, and tracking the outcome of each combat
4. Output the simulation results
    - Once the simulation is completed, output the results back to the database, with some sort of flag for the database to look for to indicate the run has been completed
