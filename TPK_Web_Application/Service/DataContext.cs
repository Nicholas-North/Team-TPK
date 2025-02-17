using Microsoft.EntityFrameworkCore;
using TPK_Web_Application.Model;

namespace TPK_Web_Application.Service
{
    public class DataContext : DbContext
    {
        public DataContext(DbContextOptions<DataContext> options) : base(options)
        {
        }

        public DbSet<Account_Model> Accounts { get; set; }
    }
}
