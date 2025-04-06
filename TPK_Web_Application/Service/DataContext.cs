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

        // Character Based tables
        public DbSet<Character_Model> Character { get; set; }
        public DbSet<Ability_Model> Abilities { get; set; }
        public DbSet<Character_Ability_Model> Character_Ability { get; set; }
        public DbSet<EncounterHistory_Model> encounterHistory { get; set; }
        public DbSet<EncounterPosition_Model> encounterPosition { get; set; }
        public DbSet<Encounter_Model> encounter { get; set; }
        public DbSet<Batch_Model> Batch { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<Account_Model>().ToTable("Account", "dbo");
            modelBuilder.Entity<Character_Model>().ToTable("character", "character");
            modelBuilder.Entity<Ability_Model>().ToTable("abilityModel", "character");
            modelBuilder.Entity<Character_Ability_Model>().ToTable("characterAbility", "character").HasKey(ca => new { ca.characterID, ca.abilityID });
            modelBuilder.Entity<EncounterHistory_Model>().ToTable("encounterHistory", "encounter");
            modelBuilder.Entity<EncounterPosition_Model>().ToTable("encounterPosition", "encounter");
            modelBuilder.Entity<Encounter_Model>().ToTable("encounter", "encounter");
            modelBuilder.Entity<Batch_Model>().ToTable("batch", "batch");
        }
    }
}
