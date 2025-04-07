using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.CharacterEditor
{
    [ApiController]
    [Route("api/CharacterAPI")]
    public class CharacterAPIController : ControllerBase
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        private readonly ILogger _logger;

        public CharacterAPIController(DataContext dataContext, SessionContext sessionContext, ILogger<CharacterAPIController> logger)
        {
            _dataContext = dataContext;
            _sessionContext = sessionContext;
            _logger = logger;
        }

        [HttpGet("GetCharacters")]
        public IActionResult GetCharacters()
        {
            try
            {
                var characters = _dataContext.Character
                    .Where(c => c.accountID == _sessionContext.Account.accountID || c.accountID == 0)
                    .ToList();
                return Ok(characters);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching characters.");
            }
        }

        [HttpGet("GetSelectedCharacters/{characterId}")]
        public IActionResult GetSelectedCharacters(long characterId)
        {
            try
            {
                var characters = _dataContext.Character
                    .Where(c => c.characterID == characterId)
                    .ToList();
                return Ok(characters);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching selected characters.");
            }
        }

        [HttpGet("GetAbilities")]
        public IActionResult GetAbilities()
        {
            try
            {
                var characters = _dataContext.Character
                    .Where(c => c.accountID == _sessionContext.Account.accountID || c.accountID == 0)
                    .ToList();

                var allAbilities = new List<Character_Ability_Model>();

                foreach (var character in characters)
                {
                    var characterAbilities = _dataContext.Character_Ability
                        .Where(c => c.characterID == character.characterID)
                        .ToList();

                    allAbilities.AddRange(characterAbilities);
                }
                return Ok(allAbilities);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching all abilities.");
            }
        }
        [HttpGet("GetSelectedCharacterAbilities/{characterId}")]
        public IActionResult GetSelectedCharacterAbilities(long characterId)
        {
            try
            {
                var selectedAbilityKeys = _dataContext.Character_Ability
                    .Where(a => a.characterID == characterId)
                    .ToList();

                var abilities = new List<Ability_Model>();

                foreach (var ability in selectedAbilityKeys)
                {
                    var matchingAbilities = _dataContext.Abilities
                        .Where(a => a.abilityID == ability.abilityID)
                        .ToList();

                    abilities.AddRange(matchingAbilities);
                    
                }
                return Ok(abilities);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching all abilities.");
            }
        }

        [HttpPut("UpdateCharacter")]
        public async Task<IActionResult> UpdateCharacter()
        {
            try
            {
                using (var reader = new StreamReader(Request.Body))
                {
                    var body = await reader.ReadToEndAsync();
                    _logger.LogInformation("Raw JSON payload: {Payload}", body);

                    try
                    {
                        // Configure case-insensitive deserialization
                        var options = new JsonSerializerOptions
                        {
                            PropertyNameCaseInsensitive = true
                        };

                        // Deserialize the JSON into the CharacterData class
                        var characterData = JsonSerializer.Deserialize<CharacterData>(body, options);

                        if (characterData == null)
                        {
                            _logger.LogWarning("Deserialization resulted in a null object. Check the JSON structure.");
                            return BadRequest("Invalid JSON structure.");
                        }

                        // Retrieve the existing character from the database
                        var character = _dataContext.Character.FirstOrDefault(c => c.characterID == characterData.Character.characterID);
                        if (character == null)
                        {
                            return NotFound("Character not found.");
                        }

                        // Update character fields
                        character.characterName = characterData.Character.characterName;
                        character.accountID = characterData.Character.accountID;
                        character.ancestry = characterData.Character.ancestry;
                        character.charLevel = characterData.Character.charLevel;
                        character.characterClass = characterData.Character.characterClass;
                        character.friendFoe = characterData.Character.friendFoe;
                        character.hp = characterData.Character.hp;
                        character.hpMax = characterData.Character.hpMax;
                        character.ac = characterData.Character.ac;
                        character.movementSpeed = characterData.Character.movementSpeed;
                        character.strScore = characterData.Character.strScore;
                        character.dexScore = characterData.Character.dexScore;
                        character.conScore = characterData.Character.conScore;
                        character.intScore = characterData.Character.intScore;
                        character.wisScore = characterData.Character.wisScore;
                        character.chaScore = characterData.Character.chaScore;
                        character.strSaveProf = characterData.Character.strSaveProf;
                        character.dexSaveProf = characterData.Character.dexSaveProf;
                        character.conSaveProf = characterData.Character.conSaveProf;
                        character.intSaveProf = characterData.Character.intSaveProf;
                        character.wisSaveProf = characterData.Character.wisSaveProf;
                        character.chaSaveProf = characterData.Character.chaSaveProf;
                        character.mainScore = characterData.Character.mainScore;
                        character.spellLevel1 = characterData.Character.spellLevel1;
                        character.spellLevel2 = characterData.Character.spellLevel2;
                        character.spellLevel3 = characterData.Character.spellLevel3;
                        character.spellLevel4 = characterData.Character.spellLevel4;
                        character.spellLevel5 = characterData.Character.spellLevel5;

                        // Update abilities
                        if (characterData.Abilities != null && characterData.Abilities.Any())
                        {
                            foreach (var ability in characterData.Abilities)
                            {
                                var existingAbility = _dataContext.Abilities.FirstOrDefault(a => a.abilityID == ability.abilityID);

                                if (existingAbility == null)
                                {
                                    // Add new ability if it doesn't exist
                                    var newAbility = new Ability_Model
                                    {
                                        abilityName = ability.abilityName,
                                        meleeRangedAOE = ability.meleeRangedAOE,
                                        rangeOne = ability.rangeOne,
                                        rangeTwo = ability.rangeTwo,
                                        radius = ability.radius,
                                        coneLineSphere = ability.coneLineSphere,
                                        actionType = ability.actionType,
                                        healTag = ability.healTag,
                                        itemToHitBonus = ability.itemToHitBonus,
                                        firstNumDice = ability.firstNumDice,
                                        firstDiceSize = ability.firstDiceSize,
                                        firstDamageType = ability.firstDamageType,
                                        secondNumDice = ability.secondNumDice,
                                        secondDiceSize = ability.secondDiceSize,
                                        secondDamageType = ability.secondDamageType,
                                        spellLevel = ability.spellLevel,
                                        saveType = ability.saveType
                                    };
                                    _dataContext.Abilities.Add(newAbility);

                                    // Link the new ability to the character
                                    _dataContext.Character_Ability.Add(new Character_Ability_Model
                                    {
                                        characterID = character.characterID,
                                        abilityID = newAbility.abilityID
                                    });
                                }
                                else
                                {
                                    // Update existing ability
                                    existingAbility.abilityName = ability.abilityName;
                                    existingAbility.meleeRangedAOE = ability.meleeRangedAOE;
                                    existingAbility.rangeOne = ability.rangeOne;
                                    existingAbility.rangeTwo = ability.rangeTwo;
                                    existingAbility.radius = ability.radius;
                                    existingAbility.coneLineSphere = ability.coneLineSphere;
                                    existingAbility.actionType = ability.actionType;
                                    existingAbility.healTag = ability.healTag;
                                    existingAbility.itemToHitBonus = ability.itemToHitBonus;
                                    existingAbility.firstNumDice = ability.firstNumDice;
                                    existingAbility.firstDiceSize = ability.firstDiceSize;
                                    existingAbility.firstDamageType = ability.firstDamageType;
                                    existingAbility.secondNumDice = ability.secondNumDice;
                                    existingAbility.secondDiceSize = ability.secondDiceSize;
                                    existingAbility.secondDamageType = ability.secondDamageType;
                                    existingAbility.spellLevel = ability.spellLevel;
                                    existingAbility.saveType = ability.saveType;
                                }
                            }
                        }

                        // Save changes to the database
                        _dataContext.SaveChanges();

                        // Return success response
                        return Ok("Character and abilities updated successfully.");
                    }
                    catch (JsonException jsonEx)
                    {
                        // Log detailed information about the deserialization error
                        _logger.LogError(jsonEx, "JSON deserialization failed. Error: {Message}", jsonEx.Message);
                        return BadRequest("Failed to deserialize JSON. Ensure the structure matches the expected format.");
                    }
                }
            }
            catch (Exception e)
            {
                _logger.LogError(e, "An unexpected error occurred while updating the character.");
                return StatusCode(500, "An error occurred while updating the character and abilities.");
            }
        }

        [HttpPost("CreateAbility")]
        public async Task<IActionResult> CreateAbility()
        {
            try
            {
                using (var reader = new StreamReader(Request.Body))
                {
                    var body = await reader.ReadToEndAsync();
                    _logger.LogInformation("Raw JSON payload: {Payload}", body);

                    try
                    {
                        // Configure case-insensitive deserialization
                        var options = new JsonSerializerOptions
                        {
                            PropertyNameCaseInsensitive = true
                        };

                        // Deserialize the JSON into a request object
                        var request = JsonSerializer.Deserialize<CreateAbilityRequest>(body, options);

                        if (request == null || request.Ability == null || request.CharacterID <= 0)
                        {
                            _logger.LogWarning("Invalid request payload.");
                            return BadRequest("Invalid request payload.");
                        }

                        // Assign a new ability ID
                        var highestAbilityID = _dataContext.Abilities
                            .OrderByDescending(a => a.abilityID)
                            .Select(a => a.abilityID)
                            .FirstOrDefault();

                        var mycharacterName = _dataContext.Character
                            .Where(c => c.characterID == request.CharacterID)
                            .Select(c => c.characterName)
                            .FirstOrDefault();

                        var newAbilityID = highestAbilityID + 1;

                        // Create the new ability
                        var newAbility = new Ability_Model
                        {
                            abilityID = newAbilityID,
                            abilityName = request.Ability.abilityName,
                            meleeRangedAOE = request.Ability.meleeRangedAOE,
                            rangeOne = request.Ability.rangeOne,
                            rangeTwo = request.Ability.rangeTwo,
                            radius = request.Ability.radius,
                            coneLineSphere = request.Ability.coneLineSphere,
                            actionType = request.Ability.actionType,
                            healTag = request.Ability.healTag,
                            itemToHitBonus = request.Ability.itemToHitBonus,
                            firstNumDice = request.Ability.firstNumDice,
                            firstDiceSize = request.Ability.firstDiceSize,
                            firstDamageType = request.Ability.firstDamageType,
                            secondNumDice = request.Ability.secondNumDice,
                            secondDiceSize = request.Ability.secondDiceSize,
                            secondDamageType = request.Ability.secondDamageType,
                            spellLevel = request.Ability.spellLevel,
                            saveType = request.Ability.saveType
                        };

                        _dataContext.Abilities.Add(newAbility);

                        // Link the new ability to the character
                        var characterAbility = new Character_Ability_Model
                        {
                            characterID = request.CharacterID,
                            abilityID = newAbilityID,
                            abilityName = request.Ability.abilityName,
                            characterName = mycharacterName
                        };

                        _dataContext.Character_Ability.Add(characterAbility);

                        // Save changes to the database
                        await _dataContext.SaveChangesAsync();

                        _logger.LogInformation("New ability created successfully: {AbilityName}", newAbility.abilityName);

                        return Ok(new { Message = "Ability created successfully.", AbilityID = newAbilityID });
                    }
                    catch (JsonException jsonEx)
                    {
                        _logger.LogError(jsonEx, "JSON deserialization failed. Error: {Message}", jsonEx.Message);
                        return BadRequest("Failed to deserialize JSON. Ensure the structure matches the expected format.");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An unexpected error occurred while creating the ability.");
                return StatusCode(500, "An error occurred while creating the ability.");
            }
        }

    }
    public class CharacterData
    {
        public Character_Model Character { get; set; } = new Character_Model(); // Represents the character's main attributes
        public List<Ability_Model> Abilities { get; set; } = new List<Ability_Model>(); // Represents the list of abilities associated with the character
    }

    public class CreateAbilityRequest
    {
        public long CharacterID { get; set; } // The ID of the character to link the ability to
        public Ability_Model Ability { get; set; } // The new ability details
    }
}