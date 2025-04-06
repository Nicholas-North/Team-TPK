using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.Text.Json;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.EncounterEditor
{
    public class EncounterEditorModel : PageModel
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        private readonly ILogger _logger;

        [BindProperty]
        public string GridData { get; set; }

        [BindProperty]
        public short XInput { get; set; }
        [BindProperty]
        public short YInput { get; set; }

        public List<Encounter_Model> Encounters { get; set; }
        public List<Character_Model> Characters { get; set; }
        [BindProperty]
        public Encounter_Model SelectedEncounter { get; set; }
        public List<EncounterPosition_Model> SelectedEncounterPositions { get; set; }
        public List<Character_Model> SelectedEncounterCharacters { get; set; }
        [BindProperty]
        public Character_Model SelectedCharacter { get; set; }
        public EncounterEditorModel(DataContext dataContext, SessionContext sessionContext, ILogger<EncounterEditorModel> logger){
            _dataContext = dataContext;
            _sessionContext = sessionContext;
            _logger = logger;

            Encounters = GetEncounters(_sessionContext.Account.accountID);
            Characters = GetCharacters(_sessionContext.Account.accountID);
        }
        public void OnGet()
        {
            try
            {
                var myencounters = _dataContext.encounter.ToList();
                foreach (var encounter in myencounters)
                {
                    Console.WriteLine($"CharacterID: {encounter.encounterID}, AccountID: {encounter.accountID}");
                }
                Encounters = GetEncounters(_sessionContext.Account.accountID);
                SelectedEncounter = Encounters.FirstOrDefault() ?? new Encounter_Model();
                PopulateSelected();
                Characters = GetCharacters(_sessionContext.Account.accountID);
                SelectedCharacter = Characters.FirstOrDefault() ?? new Character_Model();
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                SelectedEncounter = new Encounter_Model();
                SelectedCharacter = new Character_Model();
            }
        }
        public async void OnPost(int selectedEncounterId, int selectedCharacterId)
        {
            Console.WriteLine("Oops");
            SelectedEncounter = Encounters.FirstOrDefault(e => e.encounterID == selectedEncounterId) ?? new Encounter_Model();
            Console.WriteLine(SelectedEncounter.encounterID);
            PopulateSelected();
            SelectedCharacter = Characters.FirstOrDefault(c => c.characterID == selectedCharacterId) ?? new Character_Model();
        }
        public IActionResult OnPostRunEncounter()
        {
            var highestBatchID = _dataContext.Batch
                            .OrderByDescending(c => c.batchID)
                            .Select(c => c.batchID)
                            .FirstOrDefault();
            // Handle the form submission and save the encounter data
            if (SelectedEncounter.encounterID != 0)
            {
                Batch_Model batch = new Batch_Model
                {
                    batchID = highestBatchID + 1,
                    encounterID = SelectedEncounter.encounterID,
                    startTime = DateTime.Now,
                };
                _dataContext.Batch.Add(batch);
                _dataContext.SaveChanges();
                return RedirectToPage("/EncounterHistory/EncounterHistory");
            }
            //batch.batchID = 1009;
            //_dataContext.Batch.Add(batch);
            //_dataContext.SaveChanges();
            //return RedirectToPage("/EncounterEditor/EncounterEditor");
            return RedirectToPage();
        }
        public IActionResult OnPostSaveEncounter()
        {
            Console.WriteLine("HERE");
            if (!string.IsNullOrEmpty(GridData))
            {
                // Deserialize the JSON string into a list of objects
                var gridPositions = JsonSerializer.Deserialize<List<GridEntry>>(GridData);
                long highestEncounterVersion = 0;

                try
                {
                    highestEncounterVersion = _dataContext.encounterPosition
                        .Where(filter => filter.encounterID == SelectedEncounter.encounterID)
                        .Max(filter => filter.encounterVersion);
                }
                catch (InvalidOperationException)
                {
                    highestEncounterVersion = 0;
                }

                var highestUniqueCharacterID = _dataContext.encounterPosition
                    .Max(filter => filter.uniqueCharacterID);
                var highestPositionID = _dataContext.encounterPosition
                    .Max(filter => filter.positionID);
                // Process the grid positions (e.g., save to the database)
                foreach (var position in gridPositions)
                {
                    Console.WriteLine($"Position: {position}");
                    // Example: Log the positions
                    Console.WriteLine($"Character ID: {position.characterID}, X: {position.x}, Y: {position.y}");

                    EncounterPosition_Model encounterPosition = new EncounterPosition_Model
                    {
                        positionID = highestPositionID + 1,
                        encounterID = SelectedEncounter.encounterID,
                        characterID = position.characterID,
                        xloc = ((short)position.x),
                        yloc = ((short)position.y),
                        encounterVersion = highestEncounterVersion + 1,
                        uniqueCharacterID = highestUniqueCharacterID + 1
                    };

                    Console.WriteLine($"New EncounterPosition: PositionID: {encounterPosition.positionID}, " +
                        $"EncounterID: {encounterPosition.encounterID}, " +
                        $"CharacterID: {encounterPosition.characterID}, " +
                        $"X: {encounterPosition.xloc}, " +
                        $"Y: {encounterPosition.yloc}, " +
                        $"Version: {encounterPosition.encounterVersion}, " +
                        $"UniqueCharacterID: {encounterPosition.uniqueCharacterID}");

                    _dataContext.encounterPosition.Add( encounterPosition );
                    highestUniqueCharacterID += 1;
                    highestPositionID += 1;
                }
                Console.WriteLine($"SelectedEncounter: {SelectedEncounter.encounterID}");
                _dataContext.SaveChanges();
                Console.WriteLine("Encounter Positions have been successfully saved");


            }

            // Redirect or return a response
            return RedirectToPage();
        }
        public IActionResult OnPostCreateEncounter()
        {
            var highestEncounterID = _dataContext.encounter
                                        .OrderByDescending(c => c.encounterID)
                                        .Select(c => c.encounterID)
                                        .FirstOrDefault();

            // Increment the highest EncounterID by one
            var newEncounterID = highestEncounterID + 1;

            var newEncounter = new Encounter_Model
            {
                accountID = _sessionContext.Account.accountID,
                encounterID = newEncounterID,
                xdim = XInput,
                ydim = YInput
            };

            _dataContext.encounter.Add(newEncounter);
            _dataContext.SaveChanges();

            return RedirectToPage();
        }

        private List<Encounter_Model> GetEncounters(long accountID)
        {
            if (_dataContext.encounter.Count() == 0)
            {
                return new List<Encounter_Model>();
            }
            else
            {
                Console.WriteLine(accountID);
                var foundEncounters = _dataContext.encounter.Where(filter => filter.accountID == accountID).ToList();
                Console.WriteLine(foundEncounters.Count());
                return foundEncounters;
            }
        }
        private List<Character_Model> GetCharacters(long account_id)
        {
            //return empty list if list is empty
            if (_dataContext.Character.Count() == 0)
            {
                return new List<Character_Model>();
            }
            else
            {
                Console.WriteLine(account_id);
                return _dataContext.Character.Where(filter => filter.accountID == account_id || filter.accountID == 0).ToList();
            }
        }
        private List<EncounterPosition_Model> GetPositions(long encounterID)
        {
            if (_dataContext.encounterPosition.Count() == 0)
            {
                return new List<EncounterPosition_Model>();
            }
            else
            {
                var highestEncounterVersion = _dataContext.encounterPosition
                    .Where(filter => filter.encounterID == encounterID)
                    .Max(filter => filter.encounterVersion);
                Console.WriteLine($"Encounter Version: {highestEncounterVersion}");
                var foundPositions = _dataContext.encounterPosition
                    .Where(filter => filter.encounterID == encounterID && filter.encounterVersion == highestEncounterVersion)
                    .ToList();
                Console.WriteLine(foundPositions.Count());
                return foundPositions;
            }
        }
        private List<Character_Model> GetSelectedCharacters(long characterID)
        {
            if (_dataContext.encounterPosition.Count() == 0)
            {
                return new List<Character_Model>();
            }
            else
            {
                var foundCharacters = _dataContext.Character.Where(filter => filter.characterID == characterID).ToList();
                Console.WriteLine(foundCharacters.Count());
                return foundCharacters;
            }
        }
        private void PopulateSelected()
        {
            if (SelectedEncounter.encounterID != -1)
            {
                SelectedEncounterPositions = GetPositions(SelectedEncounter.encounterID);
                SelectedEncounterCharacters = GetSelectedCharacters(SelectedEncounter.encounterID);
            }
            else
            {
                SelectedEncounterPositions = new List<EncounterPosition_Model>();
                SelectedEncounterCharacters = new List<Character_Model>();
            }


        }
    }
    public class GridEntry
    {
        public int x { get; set; }
        public int y { get; set; }
        public int characterID { get; set; }
    }
}
