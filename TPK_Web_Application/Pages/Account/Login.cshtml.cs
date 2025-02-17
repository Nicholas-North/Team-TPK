using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.ComponentModel.DataAnnotations;
using System.Net;

using TPK_Web_Application.Service;

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
        public IActionResult OnPost()
        {
            if (!ModelState.IsValid)
            {
                return Page();
            }

            var user = _dataContext.Accounts.SingleOrDefault(u => u.username == Credential.UserName && u.password == Credential.Password);

            if (user != null)
            {
                // Login successful
                _sessionContext.Account.username = user.username;
                _sessionContext.Account.password = user.password;
                return RedirectToPage("/Account/Account");
            }

            // If login fails
            ModelState.AddModelError(string.Empty, "Invalid login attempt.");
            return Page();
        }
    }

    public class Credential
    {
        [Required]
        public string UserName { get; set; }

        [Required]
        [DataType(DataType.Password)]
        public string Password { get; set; }
    }
}