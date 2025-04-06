using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class Account_Model
    {
        public Account_Model()
        {
            accountID = 0;
            username = string.Empty;
            password = string.Empty;
            email = string.Empty;
            deleted = false;
        }

        [Key]
        public long accountID { get; set; }
        public string username { get; set; }
        public string password { get; set; }
        public string email {  get; set; }
        public bool deleted { get; set; }
    }
}
