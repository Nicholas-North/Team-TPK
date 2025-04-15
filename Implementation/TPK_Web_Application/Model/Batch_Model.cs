using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class Batch_Model
    {
        [Key]
        public long batchID { get; set; }
        public string batchStatus { get; set; }
        public long encounterID { get; set; }
        public long encounterVersion {  get; set; }
        public DateTime startTime { get; set; }
        public DateTime? endTime { get; set; }
        public Batch_Model()
        {
            batchID = 1003;
            batchStatus = "enqueued";
            encounterID = 1000;
            encounterVersion = 0;
            startTime = DateTime.Now;
            //endTime = DateTime.Now;
        }
    }
}