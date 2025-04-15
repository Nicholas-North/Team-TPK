using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TPK_Web_Application.Pages.Shared;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages
{
    public class IndexModel : PageModel
    {
        private readonly ILogger<IndexModel> _logger;
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;

        //public string loginText = "Login";

        public IndexModel(ILogger<IndexModel> logger, DataContext dataContext, SessionContext sessionContext)
        {
            _logger = logger;
            _dataContext = dataContext;
            _sessionContext = sessionContext;
        }

        public void OnGet()
        {
            // if (_sessionContext.Account.accountID != 0)
            // {
            //     loginText = "Welcome, " + _sessionContext.Account.username;
            // }
        }
    }
}
