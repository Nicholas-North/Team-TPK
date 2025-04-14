using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class EncounterHistory_Model
    {
        public EncounterHistory_Model(){
            batchID = -1;
            encounterID = -1;
            encounterVersion = 0;
            accountID = -1;
            team1Wins = 0;
            team2Wins = 0;
        }
        [Key]
        public long batchID { get; set; }
        public long encounterID { get; set; }
        public long encounterVersion { get; set; }
        public long accountID { get; set; }
        public double team1Wins { get; set; }
        public double team2Wins { get; set; }
    }
}
