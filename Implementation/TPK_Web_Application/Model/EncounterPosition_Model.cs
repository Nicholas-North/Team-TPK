using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class EncounterPosition_Model
    {
        [Key]
        public long positionID { get; set; }
        public long encounterID { get; set; }
        public long encounterVersion { get; set; }
        public long characterID { get; set; }
        public long uniqueCharacterID {  get; set; }
        public short xloc { get; set; }
        public short yloc { get; set; }
        public EncounterPosition_Model() 
        {
            positionID = 0;
            encounterID = 0;
            encounterVersion = 0;
            characterID = 0;
            uniqueCharacterID = 0;
            xloc = 0;
            yloc = 0;
        }
    }
}
