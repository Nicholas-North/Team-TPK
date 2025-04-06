using System.ComponentModel.DataAnnotations;

namespace TPK_Web_Application.Model
{
    public class Ability_Model()
    {
        [Key]
        public long abilityID { get; set; }
        public string abilityName { get; set; }
        public string meleeRangedAOE { get; set; }
        public bool healTag { get; set; }
        public short? itemToHitBonus { get; set; }
        public short firstNumDice { get; set; }
        public short firstDiceSize { get; set; }
        public string firstDamageType { get; set; }
        public short? secondNumDice { get; set; }
        public short? secondDiceSize { get; set; }
        public string? secondDamageType { get; set; }
        public int? rangeOne {  get; set; }
        public string? rangeTwo { get; set; }
        public int? radius {  get; set; }
        public string? coneLineSphere { get; set; }
        public short? spellLevel {  get; set; }
        public string? saveType { get; set; }
        public string actionType {  get; set; }
    }
}
