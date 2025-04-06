using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.IdentityModel.Tokens;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.CharacterEditor
{
    public class CharacterEditorModel : PageModel
    {
        private readonly ILogger<CharacterEditorModel> _logger;
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;

        [BindProperty]
        public string NameInput { get; set; }
        [BindProperty]
        public string AncestryInput { get; set; }

        // Create Character Json bound string
        [BindProperty]
        public string CharacterJson { get; set; }

        // Create Ability Json bound string
        [BindProperty]
        public string AbilityJson { get; set; }

        public List<Character_Model> Characters { get; set; }

        [BindProperty]
        public Character_Model SelectedCharacter { get; set; }
        public List<Ability_Model> BaseAbilities { get; set; }
        public List<Ability_Model> SelectedCharacterAbilities { get; set; }
        public CharacterEditorModel(ILogger<CharacterEditorModel> logger, DataContext data_context, SessionContext session_context)
        {
            _logger = logger;
            _dataContext = data_context;
            _sessionContext = session_context;

            Characters = GetCharacters(_sessionContext.Account.accountID);
        }

        public void OnGet()
        {
            try
            {
                var characters = _dataContext.Character.ToList();
                foreach (var character in characters)
                {
                    Console.WriteLine($"CharacterID: {character.characterID}, Name: {character.characterName}, AccountID: {character.accountID}");
                }
                Characters = GetCharacters(_sessionContext.Account.accountID);
                SelectedCharacter = Characters.FirstOrDefault() ?? new Character_Model();
                PopulateBaseAbilities();
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                SelectedCharacter = new Character_Model();
            }
        }

        public void OnPost(int selectedCharacterId)
        {
            Console.WriteLine("Oops");
            SelectedCharacter = Characters.FirstOrDefault(c => c.characterID == selectedCharacterId) ?? new Character_Model();
            Console.WriteLine(SelectedCharacter.characterID);
            PopulateSelectedAbilities();
        }

        public IActionResult OnPostEditCharacter()
        {
            // Print out all the values in the passed-in Character_Model
            var properties = SelectedCharacter.GetType().GetProperties();
            foreach (var property in properties)
            {
                var value = property.GetValue(SelectedCharacter) ?? "null";
                Console.WriteLine($"{property.Name}: {value}");
            }
            // Retrieve the existing character from the database
            var characterToUpdate = _dataContext.Character.FirstOrDefault(c => c.characterID == SelectedCharacter.characterID);
            if (characterToUpdate != null)
            {
                // Update the character's properties with the values from SelectedCharacter
                characterToUpdate.characterName = SelectedCharacter.characterName;
                characterToUpdate.ancestry = SelectedCharacter.ancestry;
                characterToUpdate.characterClass = SelectedCharacter.characterClass;
                characterToUpdate.charLevel = SelectedCharacter.charLevel;
                characterToUpdate.hp = SelectedCharacter.hp;
                characterToUpdate.hpMax = SelectedCharacter.hpMax;
                characterToUpdate.ac = SelectedCharacter.ac;
                characterToUpdate.movementSpeed = SelectedCharacter.movementSpeed;
                characterToUpdate.strScore = SelectedCharacter.strScore;
                characterToUpdate.dexScore = SelectedCharacter.dexScore;
                characterToUpdate.conScore = SelectedCharacter.conScore;
                characterToUpdate.intScore = SelectedCharacter.intScore;
                characterToUpdate.wisScore = SelectedCharacter.wisScore;
                characterToUpdate.chaScore = SelectedCharacter.chaScore;
                characterToUpdate.strSaveProf = SelectedCharacter.strSaveProf;
                characterToUpdate.dexSaveProf = SelectedCharacter.dexSaveProf;
                characterToUpdate.conSaveProf = SelectedCharacter.conSaveProf;
                characterToUpdate.intSaveProf = SelectedCharacter.intSaveProf;
                characterToUpdate.wisSaveProf = SelectedCharacter.wisSaveProf;
                characterToUpdate.chaSaveProf = SelectedCharacter.chaSaveProf;

                // Save the changes to the database
                _dataContext.SaveChanges();
            }

            return RedirectToPage();
        }

        public IActionResult OnPostCreateCharacter(){
            var highestCharacterID = _dataContext.Character
                .OrderByDescending(c => c.characterID)
                .Select(c => c.characterID)
                .FirstOrDefault();

            // Increment the highest characterID by one
            var newCharacterID = highestCharacterID + 1;

            var newCharacter = new Character_Model
            {
                accountID = _sessionContext.Account.accountID,
                characterID = newCharacterID,
                characterName = NameInput,
                ancestry = AncestryInput
            };

            _dataContext.Character.Add(newCharacter);
            _dataContext.SaveChanges();

            return RedirectToPage();
        }

        public IActionResult OnPostCreateAbility()
        {
            return RedirectToPage();
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
        private List<Ability_Model> PopulateBaseAbilities()
        {
            //List<Character_Ability_Model> DefaultCharacter = _dataContext.Character_Ability.Where(filter => filter.characterID == 0).ToList();
            List<Ability_Model> BaseAbilities = new List<Ability_Model>();

            //foreach (var ability in DefaultCharacter)
            //{
            //    Console.WriteLine($"Ability ID: {ability.abilityID}");
            //    var newAbility = _dataContext.Abilities.FirstOrDefault(filter => filter.abilityID == ability.abilityID);
            //    if (newAbility != null)
            //    {
            //        BaseAbilities.Add(newAbility);
            //        Console.WriteLine($"Added Ability: {newAbility.abilityName}");
            //    }
            //}

            return BaseAbilities;
        }
        private List<Ability_Model> PopulateSelectedAbilities()
        {
            //List<Character_Ability_Model> SelectedCharacterAbilities = _dataContext.Character_Ability.Where(filter => filter.characterID == SelectedCharacter.characterID).ToList();
            List<Ability_Model> CharacterAbilities = new List<Ability_Model>();

            //foreach (var ability in SelectedCharacterAbilities)
            //{
            //    Console.WriteLine($"Ability ID: {ability.abilityID}");
            //    var newAbility = _dataContext.Abilities.FirstOrDefault(filter => filter.abilityID == ability.abilityID);
            //    if (newAbility != null)
            //    {
            //        BaseAbilities.Add(newAbility);
            //        Console.WriteLine($"Added Ability: {newAbility.abilityName}");
            //    }
            //}

            return CharacterAbilities;
        }
    }

}
