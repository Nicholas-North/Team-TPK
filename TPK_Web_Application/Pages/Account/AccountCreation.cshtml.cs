using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.ComponentModel.DataAnnotations;
using TPK_Web_Application.Service;
using TPK_Web_Application.Model;

namespace TPK_Web_Application.Pages.Account
{
    public class AccountCreationModel : PageModel
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;

        [BindProperty]
        public Credential Credential { get; set; }

        public AccountCreationModel(DataContext data_context, SessionContext session_context)
        {
            _dataContext = data_context;
            _sessionContext = session_context;
        }

        public IActionResult OnPost()
        {
            if (!ModelState.IsValid)
            {
                return Page();
            }

            var user = _dataContext.Accounts.SingleOrDefault(u => u.username == Credential.UserName);

            if (user == null)
            {
                var maxAccountId = _dataContext.Accounts.Max(u => (int?)u.accountID) ?? 0;
                var newAccountId = maxAccountId + 1;

                var newUser = new Account_Model
                {
                    username = Credential.UserName,
                    password = Credential.Password,
                    email = Credential.Email,
                    accountID = newAccountId
                };

                _dataContext.Accounts.Add(newUser);
                _dataContext.SaveChanges();

                _sessionContext.Account.username = newUser.username;
                _sessionContext.Account.password = newUser.password;
                _sessionContext.Account.email = newUser.email;
                _sessionContext.Account.accountID = newUser.accountID;
                _sessionContext.Account.deleted = newUser.deleted;
                _sessionContext.IsAuthenticated = true;
                return RedirectToPage("/Account/Account");
            }

            // Add your account creation logic here
            ModelState.AddModelError(string.Empty, "User already exists. Please try a different user name");
            return Page();
        }
    }
}