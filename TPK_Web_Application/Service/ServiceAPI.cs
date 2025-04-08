using Microsoft.AspNetCore.Mvc;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Service
{
    [ApiController]
    [Route("api/ServiceAPI")]
    public class ServiceAPIController : ControllerBase
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        private readonly ILogger _logger;

        public ServiceAPIController(DataContext dataContext, SessionContext sessionContext, ILogger<ServiceAPIController> logger)
        {
            _dataContext = dataContext;
            _sessionContext = sessionContext;
            _logger = logger;
        }

        [HttpGet("GetAuthenticated")]
        public IActionResult GetAuthenticated()
        {
            try
            {
                return Ok(_sessionContext.IsAuthenticated);
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while fetching authenticated");
            }
        }

        [HttpPost("PostAuthenticatedTrue")]
        public IActionResult PostAuthenticatedTrue()
        {
            try
            {
                _sessionContext.IsAuthenticated = true;

                return Ok();
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while updating auth to true");
            }
        }
        [HttpPost("PostAuthenticatedFalse")]
        public IActionResult PostAuthenticatedFalse()
        {
            try
            {
                _sessionContext.IsAuthenticated = false;

                return Ok();
            }
            catch (Exception e)
            {
                _logger.LogError(e.Message);
                return StatusCode(500, "An error occurred while updating auth to false");
            }
        }
    }
}