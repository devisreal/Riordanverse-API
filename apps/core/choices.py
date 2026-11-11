# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------
SERIES_CHOICES = (
    ('percy_jackson_and_the_olympians', 'Percy Jackson & the Olympians'),
    ('heroes_of_olympus', 'Heroes of Olympus'),
    ('kane_chronicles', 'The Kane Chronicles'),
    ('trials_of_apollo', 'The Trials of Apollo'),
    ('magnus_chase', 'Magnus Chase and the Gods of Asgard'),
    ('nico_di_angelo_adventures', 'The Nico di Angelo Adventures'),
    ('senior_year_adventures', 'The Senior Year Adventures'),
    ('companion', 'Companion Book'),
    ('short_story', 'Short Story'),
)

# ---------------------------------------------------------------------------
# Book Type
# ---------------------------------------------------------------------------
BOOK_TYPE_CHOICES = (
    ('novel', 'Novel'),
    ('companion_book', 'Companion Book'),
    ('short_story_collection', 'Short Story Collection'),
    ('short_story', 'Short Story'),
    ('myth_anthology', 'Myth Anthology'),
    ('graphic_novel', 'Graphic Novel'),
)

# ---------------------------------------------------------------------------
# Character Type
# ---------------------------------------------------------------------------
CHARACTER_TYPE_CHOICES = (
    ('demigod', 'Demigod'),
    ('god', 'God'),
    ('titan', 'Titan'),
    ('monster', 'Monster'),
    ('creature', 'Creature'),
    ('mortal', 'Mortal'),
    ('satyr', 'Satyr'),
    ('centaur', 'Centaur'),
    ('cyclops', 'Cyclops'),
    ('nymph', 'Nymph'),
    ('hunter', 'Hunter'),
    ('oracle', 'Oracle'),
    ('legacy', 'Legacy'),
    ('automaton', 'Automaton'),
    ('spirit', 'Spirit'),
    ('primordial', 'Primordial'),
)

# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------
SPECIES_CHOICES = (
    ('human', 'Human'),
    ('demigod', 'Demigod'),
    ('satyr', 'Satyr'),
    ('centaur', 'Centaur'),
    ('cyclops', 'Cyclops'),
    ('pegasus', 'Pegasus'),
    ('nymph', 'Nymph'),
    ('naiad', 'Naiad'),
    ('nereid', 'Nereid'),
    ('harpy', 'Harpy'),
    ('fury', 'Fury'),
    ('gorgon', 'Gorgon'),
    ('dracaena', 'Dracaena'),
    ('telekhine', 'Telekhine'),
    ('giant', 'Giant'),
    ('automaton', 'Automaton'),
    ('spirit', 'Spirit'),
    ('hekatonkheir', 'Hekatonkheir'),
    ('other', 'Other'),
)

# ---------------------------------------------------------------------------
# Gender
# ---------------------------------------------------------------------------
GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('non_binary', 'Non-Binary'),
    ('unknown', 'Unknown'),
)

# ---------------------------------------------------------------------------
# Status (characters, titans, gods)
# ---------------------------------------------------------------------------
STATUS_CHOICES = (
    ('alive', 'Alive'),
    ('deceased', 'Deceased'),
    ('immortal', 'Immortal'),
    ('transformed', 'Transformed'),
    ('imprisoned', 'Imprisoned'),
    ('faded', 'Faded'),
    ('unknown', 'Unknown'),
)

# ---------------------------------------------------------------------------
# Greek / Roman alignment
# ---------------------------------------------------------------------------
GREEK_OR_ROMAN_CHOICES = (
    ('greek', 'Greek'),
    ('roman', 'Roman'),
    ('both', 'Both'),
    ('neither', 'Neither'),
)

# ---------------------------------------------------------------------------
# Affiliation
# ---------------------------------------------------------------------------
AFFILIATION_CHOICES = (
    ('camp_half_blood', 'Camp Half-Blood'),
    ('hunters_of_artemis', 'Hunters of Artemis'),
    ('olympian_council', 'Olympian Council'),
    ('titan_army', 'Titan Army'),
    ('neutral', 'Neutral'),
    ('underworld', 'Underworld'),
    ('council_of_cloven_elders', 'Council of Cloven Elders'),
    ('kronos_army', "Kronos's Army"),
)

# ---------------------------------------------------------------------------
# God Tier
# ---------------------------------------------------------------------------
GOD_TIER_CHOICES = (
    ('olympian', 'Olympian'),
    ('minor', 'Minor God'),
    ('chthonic', 'Chthonic'),
    ('primordial', 'Primordial'),
    ('river_god', 'River God'),
    ('nature_deity', 'Nature Deity'),
)

# ---------------------------------------------------------------------------
# God Oath Status (Big Three oath)
# ---------------------------------------------------------------------------
OATH_STATUS_CHOICES = (
    ('bound_by_oath', 'Bound by Oath'),
    ('oath_dissolved', 'Oath Dissolved'),
    ('exempt', 'Exempt'),
    ('not_applicable', 'Not Applicable'),
)

# ---------------------------------------------------------------------------
# God Affiliation
# ---------------------------------------------------------------------------
GOD_AFFILIATION_CHOICES = (
    ('olympian_council', 'Olympian Council'),
    ('neutral', 'Neutral'),
    ('titan_allied', 'Titan Allied'),
    ('chthonic', 'Chthonic'),
    ('independent', 'Independent'),
)

# ---------------------------------------------------------------------------
# Titan Generation
# ---------------------------------------------------------------------------
TITAN_GENERATION_CHOICES = (
    ('elder_titan', 'Elder Titan'),
    ('younger_titan', 'Younger Titan'),
)

# ---------------------------------------------------------------------------
# Titan Alignment
# ---------------------------------------------------------------------------
TITAN_ALIGNMENT_CHOICES = (
    ('kronos_army', "Kronos's Army"),
    ('neutral', 'Neutral'),
    ('olympian_allied', 'Olympian Allied'),
    ('independent', 'Independent'),
)

# ---------------------------------------------------------------------------
# Monster Type
# ---------------------------------------------------------------------------
MONSTER_TYPE_CHOICES = (
    ('gorgon', 'Gorgon'),
    ('cyclops', 'Cyclops'),
    ('giant', 'Giant'),
    ('sea_monster', 'Sea Monster'),
    ('underworld_creature', 'Underworld Creature'),
    ('chimeric', 'Chimeric'),
    ('undead', 'Undead'),
    ('nature_spirit', 'Nature Spirit'),
    ('shapeshifter', 'Shapeshifter'),
    ('mechanical', 'Mechanical'),
    ('bovine_humanoid', 'Bovine Humanoid'),
    ('fury', 'Fury'),
    ('hybrid_monster', 'Hybrid Monster'),
    ('swamp_hydra', 'Swamp Hydra'),
    ('manticore', 'Manticore'),
    ('mythic_beast', 'Mythic Beast'),
    ('dragon', 'Dragon'),
    ('ancient_dragon_jailer', 'Ancient Dragon Jailer'),
    ('empousa', 'Empousa'),
    ('drakon', 'Drakon'),
)

# ---------------------------------------------------------------------------
# Monster Allegiance
# ---------------------------------------------------------------------------
MONSTER_ALLEGIANCE_CHOICES = (
    ('kronos_army', "Kronos's Army"),
    ('olympian_ally', 'Olympian Ally'),
    ('neutral', 'Neutral'),
    ('independent', 'Independent'),
    ('hades_servant', "Hades's Servant"),
)

# ---------------------------------------------------------------------------
# Weapon Type
# ---------------------------------------------------------------------------
WEAPON_TYPE_CHOICES = (
    ('sword', 'Sword'),
    ('spear', 'Spear'),
    ('dagger', 'Dagger'),
    ('bow', 'Bow'),
    ('shield', 'Shield'),
    ('trident', 'Trident'),
    ('scythe', 'Scythe'),
    ('club', 'Club'),
    ('staff', 'Staff'),
    ('helm', 'Helm'),
    ('whip', 'Whip'),
    ('arrows', 'Arrows'),
    ('magical_item', 'Magical Item'),
    ('artifact', 'Artifact'),
)

# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------
MATERIAL_CHOICES = (
    ('celestial_bronze', 'Celestial Bronze'),
    ('composite', 'Composite'),
    ('flint', 'Flint'),
    ('gold', 'Gold'),
    ('other', 'Other'),
    ('stygian_iron', 'Stygian Iron'),
    ('imperial_gold', 'Imperial Gold'),
    ('mortal_steel', 'Mortal Steel'),
    ('silver', 'Silver'),
    ('divine_material', 'Divine Material'),
    ('enchanted', 'Enchanted'),
    ('wood', 'Wood'),
)

# ---------------------------------------------------------------------------
# Location Type
# ---------------------------------------------------------------------------
LOCATION_TYPE_CHOICES = (
    ('camp', 'Camp'),
    ('olympus', 'Olympus'),
    ('underworld', 'Underworld'),
    ('mortal_city', 'Mortal City'),
    ('mythical_island', 'Mythical Island'),
    ('labyrinth', 'Labyrinth'),
    ('sea', 'Sea'),
    ('mountain', 'Mountain'),
    ('forest', 'Forest'),
    ('hotel_or_building', 'Hotel or Building'),
    ('divine_realm', 'Divine Realm'),
    ('crossroads', 'Crossroads'),
)

# ---------------------------------------------------------------------------
# Event Type
# ---------------------------------------------------------------------------
EVENT_TYPE_CHOICES = (
    ('battle', 'Battle'),
    ('war', 'War'),
    ('quest_event', 'Quest Event'),
    ('political_event', 'Political Event'),
    ('sacrifice', 'Sacrifice'),
)

EVENT_DATE_PRECISION_CHOICES = (
    ('exact', 'Exact'),
    ('approximate', 'Approximate'),
    ('relative_period', 'Relative Period'),
    ('mythological_era', 'Mythological Era'),
    ('disputed', 'Disputed'),
    ('unknown', 'Unknown'),
)

# ---------------------------------------------------------------------------
# Faction Type
# ---------------------------------------------------------------------------
FACTION_TYPE_CHOICES = (
    ('camp', 'Camp'),
    ('army', 'Army'),
    ('order', 'Order'),
    ('group', 'Group'),
    ('council', 'Council'),
    ('family', 'Family'),
)

# ---------------------------------------------------------------------------
# Image — Source Type
# ---------------------------------------------------------------------------
IMAGE_SOURCE_TYPE_CHOICES = (
    ('official_book', 'Official Book'),
    ('official_publisher', 'Official Publisher'),
    ('disney_plus', 'Disney+'),
    ('official_game', 'Official Game'),
    ('fan_art', 'Fan Art'),
    ('wiki', 'Wiki'),
    ('unknown', 'Unknown'),
)

# ---------------------------------------------------------------------------
# Image — Category
# ---------------------------------------------------------------------------
IMAGE_CATEGORY_CHOICES = (
    ('portrait', 'Portrait'),
    ('full_body', 'Full Body'),
    ('action', 'Action'),
    ('weapon_closeup', 'Weapon Close-Up'),
    ('location', 'Location'),
    ('book_cover', 'Book Cover'),
    ('concept_art', 'Concept Art'),
    ('promotional', 'Promotional'),
    ('other', 'Other'),
)
