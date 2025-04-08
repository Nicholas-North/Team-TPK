using Microsoft.AspNetCore.Mvc;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.EncounterHistory
{
    [ApiController]
    [Route("api/EncounterHistoryAPI")]
    public class EncounterHistoryAPIController : ControllerBase
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        private readonly ILogger _logger;

        public EncounterHistoryAPIController(DataContext dataContext, SessionContext sessionContext, ILogger<EncounterHistoryAPIController> logger)
        {
            _dataContext = dataContext;
            _sessionContext = sessionContext;
            _logger = logger;
        }

        [HttpGet("GetHistory")]
        public IActionResult GetHistory()
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
        [HttpGet("GetSelectedHistory")]
        public IActionResult GetSelectedHistory([FromBody] SelectedHistoryRequest request)
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
    }
    public class SelectedHistoryRequest
    {
        public int EncounterID { get; set; }
        public string Version { get; set; }
        public int BatchID { get; set; }
    }
}