using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.Collections.Generic;
using System.Linq;
using TPK_Web_Application.Model;
using TPK_Web_Application.Service;

namespace TPK_Web_Application.Pages.EncounterHistory
{
    public class EncounterHistoryPageModel : PageModel
    {
        private readonly SessionContext _sessionContext;
        private readonly DataContext _dataContext;

        public EncounterHistory_Model selectedEncounter {  get; set; }
        public Batch_Model batch { get; set; }
        public List<EncounterHistory_Model> History { get; set; }
        public List<Batch_Model> Batches { get; set; }

        public EncounterHistoryPageModel(DataContext dataContext, SessionContext sessionContext)
        {
            _sessionContext = sessionContext;
            _dataContext = dataContext;

            OnGet();
        }

        public void OnGet()
        {
            History = _dataContext.encounterHistory
                .Where(m => m.accountID == _sessionContext.Account.accountID)
                .ToList();

            selectedEncounter = History.FirstOrDefault() ?? new EncounterHistory_Model();

            // batch = _dataContext.Batch.Where(x => x.batchID == History.)
        }
        public IActionResult OnPost()
        {
            var batchId = int.Parse(Request.Form["selectedBatchId"]);
            selectedEncounter = History.SingleOrDefault(e => e.batchID == batchId);
            return Page();
        }
    }
}
