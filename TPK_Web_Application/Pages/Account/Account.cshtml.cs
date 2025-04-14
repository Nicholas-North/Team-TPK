using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.Account
{
    public class AccountModel : PageModel
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;
        public string Username { get; set; } 
        public string Password { get; set; } 
        public string Email { get; set; } 

        public AccountModel(SessionContext sessionContext, DataContext dataContext)
        {
            _sessionContext = sessionContext;
            _dataContext = dataContext;

            Username = _sessionContext.Account.username;
            Password = _sessionContext.Account.password;
            Email = _sessionContext.Account.email;
        }

        public void OnGet()
        {
            Username = _sessionContext.Account.username;
            Password = _sessionContext.Account.password;
            Email = _sessionContext.Account.email;
        }

        public IActionResult OnPostSignOut()
        {
            // Add your sign-out logic here
            _sessionContext.Account.username = "";
            _sessionContext.Account.password = "";
            _sessionContext.Account.email = "";
            _sessionContext.Account.accountID = 0;
            _sessionContext.Account.deleted = false;
            _sessionContext.IsAuthenticated = false;
            return RedirectToPage("/Index");
        }

        public IActionResult OnPostDeleteAccount()
        {
            // Add your delete account logic here
            if (_sessionContext.Account.accountID != 0)
            {
                var account = _dataContext.Accounts.SingleOrDefault(a => a.accountID == _sessionContext.Account.accountID);
                if (account != null)
                {
                    account.deleted = true;
                    _dataContext.Accounts.Update(account);
                    _dataContext.SaveChanges();
                }
            }
            _sessionContext.Account.deleted = true;
            return RedirectToPage("/Index");
        }
    }
}