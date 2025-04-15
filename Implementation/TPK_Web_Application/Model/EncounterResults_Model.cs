namespace TPK_Web_Application.Model
{
    public class EncounterResults_Model
    {
        public long batchID { get; set; }
        public long encounterID { get; set; }
        public long encounterVersion { get; set; }
        public string resultData { get; set; }
        public DateTime timestamp { get; set; }
    }
}
