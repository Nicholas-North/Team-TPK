using System.ComponentModel.DataAnnotations;
using System.Text;

namespace TPK_Web_Application.Model
{
    public class Character_Model
    {
        [Key]
        // Base characteristics
        public long characterID { get; set; }
        public long accountID { get; set; }
        public short hpMax { get; set; }
        public short hp { get; set; }
        public short ac { get; set; }
        public short movementSpeed { get; set; }
        public short charLevel { get; set; }
        public int proficiencyBonus { get; set; }
        public short strScore { get; set; }
        public short dexScore { get; set; }
        public short conScore { get; set; }
        public short intScore { get; set; }
        public short wisScore { get; set; }
        public short chaScore { get; set; }
        public string characterName { get; set; }
        public string characterClass { get; set; }
        public string ancestry { get; set; }
        public bool strSaveProf { get; set; }
        public bool dexSaveProf { get; set; }
        public bool conSaveProf { get; set; }
        public bool intSaveProf { get; set; }
        public bool wisSaveProf { get; set; }
        public bool chaSaveProf { get; set; }
        public int? spellLevel1 { get; set; }
        public int? spellLevel2 { get; set; } 
        public int? spellLevel3 { get; set; }
        public int? spellLevel4 { get; set; }
        public int? spellLevel5 { get; set; }
        public string mainScore { get; set; }
        public bool? friendFoe {  get; set; }
        public byte[]? charToken { get; set; }

        public Character_Model(){
            characterID = 0;
            accountID = 0;
            hpMax = 0;
            hp = 0;
            ac = 0;
            movementSpeed = 0;
            charLevel = 0;
            proficiencyBonus = 0;
            strScore = 0;
            dexScore = 0;
            conScore = 0;
            intScore = 0;
            wisScore = 0;
            chaScore = 0;
            characterName = "";
            characterClass = "";
            ancestry = "";
            strSaveProf = false;
            dexSaveProf = false;
            conSaveProf = false;
            intSaveProf = false;
            wisSaveProf = false;
            chaSaveProf = false;
            spellLevel1 = 0;
            spellLevel2 = 0;
            spellLevel3 = 0;
            spellLevel4 = 0;
            spellLevel5 = 0;
            mainScore = "";
            friendFoe = false;
            charToken = Encoding.UTF8.GetBytes("");
        }
    }
}
