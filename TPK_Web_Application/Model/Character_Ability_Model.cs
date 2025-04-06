using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TPK_Web_Application.Model
{
    public class Character_Ability_Model()
    {
        [Key, Column(Order = 0)]
        public long characterID {  get; set; }
        [Key, Column(Order = 1)]
        public long abilityID { get; set; }
        public string characterName { get; set; }
        public string abilityName { get; set; }
    }
}
