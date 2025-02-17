using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class Account_Model
    {
        [Key]
        public int account_id { get; set; }
        public string username { get; set; }
        public string password { get; set; }
    }
}
