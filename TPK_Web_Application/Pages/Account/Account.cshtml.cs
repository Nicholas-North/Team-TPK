using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.Account
{
    public class AccountModel : PageModel
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        public string Username { get; set; } = "CurrentUsername";
        public string Password { get; set; } = "CurrentPassword";
        public string Email { get; set; } = "CurrentEmail@example.com";

        public AccountModel(SessionContext sessionContext)
        {
            _sessionContext = sessionContext;
        }

        public void OnGet()
        {
        }

        public IActionResult OnPostSignOut()
        {
            // Add your sign-out logic here
            return RedirectToPage("/Index");
        }

        public IActionResult OnPostDeleteAccount()
        {
            // Add your delete account logic here
            return RedirectToPage("/Index");
        }
    }
}