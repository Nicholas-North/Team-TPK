using Microsoft.AspNetCore.Mvc;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.EncounterEditor
{
    [ApiController]
    [Route("api/EncounterAPI")]
    public class EncounterAPIController : ControllerBase
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        private readonly ILogger _logger;

        public EncounterAPIController(DataContext dataContext, SessionContext sessionContext, ILogger<EncounterAPIController> logger)
        {
            _dataContext = dataContext;
            _sessionContext = sessionContext;
            _logger = logger;
        }

        [HttpGet("GetEncounters")]
        public IActionResult GetEncounters()
        {
            try
            {
                var encounters = _dataContext.encounter
                    .Where(e => e.accountID == _sessionContext.Account.accountID)
                    .ToList();
                return Ok(encounters);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching encounters.");
            }
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

        [HttpPost("CreateEncounter")]
        public IActionResult CreateEncounter([FromBody] Encounter_Model newEncounter)
        {
            try
            {
                var highestEncounterID = _dataContext.encounter
                    .OrderByDescending(e => e.encounterID)
                    .Select(e => e.encounterID)
                    .FirstOrDefault();

                newEncounter.encounterID = highestEncounterID + 1;
                newEncounter.accountID = _sessionContext.Account.accountID;

                _dataContext.encounter.Add(newEncounter);
                _dataContext.SaveChanges();

                return Ok(newEncounter);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while creating the encounter.");
            }
        }

        [HttpPost("RunEncounter")]
        public IActionResult RunEncounter([FromBody] int selectedEncounterId)
        {
            try
            {
                var highestBatchID = _dataContext.Batch
                    .OrderByDescending(b => b.batchID)
                    .Select(b => b.batchID)
                    .FirstOrDefault();

                long highestEncounterVersion = 0;
                try
                {
                    highestEncounterVersion = _dataContext.encounterPosition
                        .Where(filter => filter.encounterID == selectedEncounterId)
                        .Max(filter => filter.encounterVersion);
                }
                catch (InvalidOperationException)
                {
                    highestEncounterVersion = 0;
                }

                if (selectedEncounterId != 0)
                {
                    var batch = new Batch_Model
                    {
                        batchID = highestBatchID + 1,
                        encounterID = selectedEncounterId,
                        encounterVersion = highestEncounterVersion,
                        startTime = DateTime.Now,
                    };

                    _dataContext.Batch.Add(batch);
                    _dataContext.SaveChanges();

                    _logger.LogInformation($"Encounter {selectedEncounterId} successfully started with Batch ID {batch.batchID}.");
                    return Ok(new { message = "Encounter started successfully.", batchId = batch.batchID });
                }

                return BadRequest("Invalid encounter ID.");
            }
            catch (Exception e)
            {
                _logger.LogError(e, "An error occurred while running the encounter.");
                return StatusCode(500, "An error occurred while running the encounter.");
            }
        }

        [HttpGet("GetPositions/{encounterId}")]
        public IActionResult GetPositions(long encounterId)
        {
            try
            {
                var highestEncounterVersion = _dataContext.encounterPosition
                    .Where(filter => filter.encounterID == encounterId)
                    .Max(filter => filter.encounterVersion);
                var positions = _dataContext.encounterPosition
                    .Where(p => p.encounterID == encounterId && p.encounterVersion == highestEncounterVersion)
                    .ToList();
                return Ok(positions);
            }
            catch (InvalidOperationException)
            {
                return Ok(new List<object>());
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching positions.");
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

        [HttpGet("GetSelectedEncounter/{encounterId}")]
        public IActionResult GetSelectedEncounter(long encounterId)
        {
            try
            {
                var encounter = _dataContext.encounter
                    .FirstOrDefault(e => e.encounterID == encounterId);

                if (encounter == null)
                {
                    return NotFound($"Encounter with ID {encounterId} not found.");
                }

                return Ok(encounter);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching the selected encounter.");
            }
        }
    }
}