using Microsoft.AspNetCore.Mvc.RazorPages;

namespace TPK_Web_Application.Pages.Shared
{
    public class BasePageModel : PageModel
    {
        public string loginText { get; set; } = "Login";

        public void OnGet()
        {
            // Add any logic you want to run on every page
        }
    }
}