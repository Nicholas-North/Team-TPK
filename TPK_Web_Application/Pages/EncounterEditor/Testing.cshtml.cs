using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.IdentityModel.Tokens;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.EncounterEditor
{
    public class TestingModel : PageModel
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        public TestingModel(DataContext dataContext, SessionContext sessionContext)
        {
            _dataContext = dataContext;
            _sessionContext = sessionContext;
        }
        public void OnGet()
        {
        }
    }
}
