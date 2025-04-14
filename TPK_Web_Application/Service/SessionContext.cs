using TPK_Web_Application.Model;

namespace TPK_Web_Application.Service
{
    public class SessionContext
    {
        public SessionContext() 
        {
            IsAuthenticated = false;
            Account = new Account_Model();
        }

        public bool IsAuthenticated { get; set; }
        public Account_Model Account { get; set; }
    }
}
