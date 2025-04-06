using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TPK_Web_Application.Service;
using TPK_Web_Application.Model;
using TPK_Web_Application.Pages.Shared;

namespace TPK_Web_Application.Pages.Account
{
    public class LoginModel : PageModel
    {
        private readonly DataContext _dataContext;
        private readonly SessionContext _sessionContext;

        public LoginModel(DataContext data_context, SessionContext session_context)
        {
            _dataContext = data_context;
            _sessionContext = session_context;
        }

        [BindProperty]
        public Credential Credential { get; set; }
        public void OnGet()
        {
            //this.Credential = new Credential { UserName = "admin" };
        }
        public IActionResult OnPostLogin()
        {
            ModelState.Remove("Credential.Email");
            if (!ModelState.IsValid)
            {
                var errors = ModelState.Values.SelectMany(v => v.Errors);
                foreach (var error in errors)
                {
                    Console.WriteLine(error.ErrorMessage);
                }
                return Page();
            }
            Console.WriteLine(Credential.UserName);
            var user = _dataContext.Accounts.SingleOrDefault(u => u.username == Credential.UserName && u.password == Credential.Password);

            // TODO: Fix if user misinputs here.
            if (user.deleted == true)
            {
                ModelState.AddModelError(string.Empty, "Account has been deleted.");
                return Page();
            }

            if (user != null)
            {
                _sessionContext.Account.username = user.username;
                _sessionContext.Account.password = user.password;
                _sessionContext.Account.email = user.email;
                _sessionContext.Account.accountID = user.accountID;
                return RedirectToPage("/Account/Account");
            }

            // If login fails
            ModelState.AddModelError(string.Empty, "Invalid login attempt.");
            return Page();
        }

        public IActionResult OnPostCreateAccount()
        {
            return RedirectToPage("/Account/AccountCreation");
        }
    }
}