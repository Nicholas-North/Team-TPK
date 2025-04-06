using Microsoft.AspNetCore.Mvc;
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
    }
}