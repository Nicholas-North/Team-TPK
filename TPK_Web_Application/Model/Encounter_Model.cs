using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class Encounter_Model
    {
        [Key]
        public long encounterID { get; set; }
        public long accountID { get; set; }
        public short xdim { get; set; }
        public short ydim { get; set; }
        public bool randomPosition { get; set; }
        public Encounter_Model()
        {
            encounterID = 0;
            accountID = 0;
            xdim = 0;
            ydim = 0;
            randomPosition = false;
        }
    }
}
