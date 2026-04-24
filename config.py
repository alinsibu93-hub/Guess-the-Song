"""
config.py — Central configuration for Guess the Song.

Song library: 303 curated tracks across 9 genres × 5 eras.
Each entry is a dict with keys: artist, title, genre, era.
"""

from dataclasses import dataclass
from typing import Dict, List


# ── Genre / era constants ──────────────────────────────────────────────────

GENRES = ["pop", "rock", "hiphop", "rb", "electronic", "metal", "indie", "latin", "kpop"]

ERAS = ["80s", "90s", "2000s", "2010s", "2020s"]

GENRE_LABELS: Dict[str, str] = {
    "pop":        "Pop",
    "rock":       "Rock",
    "hiphop":     "Hip-Hop",
    "rb":         "R&B",
    "electronic": "Electronic",
    "metal":      "Metal",
    "indie":      "Indie",
    "latin":      "Latin",
    "kpop":       "K-Pop",
}

ERA_LABELS: Dict[str, str] = {
    "80s":   "80s",
    "90s":   "90s",
    "2000s": "2000s",
    "2010s": "2010s",
    "2020s": "2020s",
}

# When the selected genre/era pool has fewer songs than needed,
# fall back to these related genres (in order of preference).
RELATED_GENRES: Dict[str, List[str]] = {
    "pop":        ["indie", "electronic", "kpop"],
    "rock":       ["metal", "indie"],
    "hiphop":     ["rb"],
    "rb":         ["hiphop", "pop"],
    "electronic": ["pop", "indie"],
    "metal":      ["rock", "indie"],
    "indie":      ["pop", "rock", "electronic"],
    "latin":      ["pop"],
    "kpop":       ["pop", "electronic"],
}


# ── Song library ───────────────────────────────────────────────────────────
#
# 303 songs (Pop×48, Rock×36, Hip-Hop×42, R&B×36, Electronic×34,
#            Metal×26, Indie×30, Latin×28, K-Pop×23).
#
# Keys: artist (str), title (str), genre ∈ GENRES, era ∈ ERAS

SONG_LIBRARY: List[Dict[str, str]] = [

    # ── Pop 80s (10) ──────────────────────────────────────────────────────
    {"artist": "Michael Jackson",       "title": "Thriller",                        "genre": "pop",        "era": "80s"},
    {"artist": "Michael Jackson",       "title": "Beat It",                         "genre": "pop",        "era": "80s"},
    {"artist": "Madonna",               "title": "Like a Virgin",                   "genre": "pop",        "era": "80s"},
    {"artist": "Madonna",               "title": "Material Girl",                   "genre": "pop",        "era": "80s"},
    {"artist": "Whitney Houston",       "title": "I Wanna Dance with Somebody",     "genre": "pop",        "era": "80s"},
    {"artist": "Cyndi Lauper",          "title": "Girls Just Want to Have Fun",     "genre": "pop",        "era": "80s"},
    {"artist": "Prince",                "title": "When Doves Cry",                  "genre": "pop",        "era": "80s"},
    {"artist": "George Michael",        "title": "Faith",                           "genre": "pop",        "era": "80s"},
    {"artist": "Tina Turner",           "title": "What's Love Got to Do with It",   "genre": "pop",        "era": "80s"},
    {"artist": "Lionel Richie",         "title": "Hello",                           "genre": "pop",        "era": "80s"},

    # ── Pop 90s (10) ──────────────────────────────────────────────────────
    {"artist": "Backstreet Boys",       "title": "I Want It That Way",              "genre": "pop",        "era": "90s"},
    {"artist": "NSYNC",                 "title": "Bye Bye Bye",                     "genre": "pop",        "era": "90s"},
    {"artist": "Britney Spears",        "title": "Baby One More Time",              "genre": "pop",        "era": "90s"},
    {"artist": "Mariah Carey",          "title": "Fantasy",                         "genre": "pop",        "era": "90s"},
    {"artist": "Celine Dion",           "title": "My Heart Will Go On",             "genre": "pop",        "era": "90s"},
    {"artist": "Spice Girls",           "title": "Wannabe",                         "genre": "pop",        "era": "90s"},
    {"artist": "Savage Garden",         "title": "Truly Madly Deeply",              "genre": "pop",        "era": "90s"},
    {"artist": "Destiny's Child",       "title": "Say My Name",                     "genre": "pop",        "era": "90s"},
    {"artist": "Robbie Williams",       "title": "Angels",                          "genre": "pop",        "era": "90s"},
    {"artist": "No Doubt",              "title": "Don't Speak",                     "genre": "pop",        "era": "90s"},

    # ── Pop 2000s (10) ────────────────────────────────────────────────────
    {"artist": "Beyoncé",               "title": "Crazy in Love",                   "genre": "pop",        "era": "2000s"},
    {"artist": "Nelly Furtado",         "title": "Maneater",                        "genre": "pop",        "era": "2000s"},
    {"artist": "Kelly Clarkson",        "title": "Since U Been Gone",               "genre": "pop",        "era": "2000s"},
    {"artist": "Justin Timberlake",     "title": "SexyBack",                        "genre": "pop",        "era": "2000s"},
    {"artist": "Rihanna",               "title": "Umbrella",                        "genre": "pop",        "era": "2000s"},
    {"artist": "Katy Perry",            "title": "I Kissed a Girl",                 "genre": "pop",        "era": "2000s"},
    {"artist": "Lady Gaga",             "title": "Just Dance",                      "genre": "pop",        "era": "2000s"},
    {"artist": "Gwen Stefani",          "title": "Hollaback Girl",                  "genre": "pop",        "era": "2000s"},
    {"artist": "Shakira",               "title": "Hips Don't Lie",                  "genre": "pop",        "era": "2000s"},
    {"artist": "Britney Spears",        "title": "Toxic",                           "genre": "pop",        "era": "2000s"},

    # ── Pop 2010s (10) ────────────────────────────────────────────────────
    {"artist": "Taylor Swift",          "title": "Shake It Off",                    "genre": "pop",        "era": "2010s"},
    {"artist": "Katy Perry",            "title": "Roar",                            "genre": "pop",        "era": "2010s"},
    {"artist": "Ariana Grande",         "title": "Problem",                         "genre": "pop",        "era": "2010s"},
    {"artist": "The Weeknd",            "title": "Blinding Lights",                 "genre": "pop",        "era": "2010s"},
    {"artist": "Ed Sheeran",            "title": "Shape of You",                    "genre": "pop",        "era": "2010s"},
    {"artist": "Justin Bieber",         "title": "Sorry",                           "genre": "pop",        "era": "2010s"},
    {"artist": "Selena Gomez",          "title": "Come & Get It",                   "genre": "pop",        "era": "2010s"},
    {"artist": "Dua Lipa",              "title": "New Rules",                       "genre": "pop",        "era": "2010s"},
    {"artist": "Miley Cyrus",           "title": "Wrecking Ball",                   "genre": "pop",        "era": "2010s"},
    {"artist": "Bruno Mars",            "title": "Uptown Funk",                     "genre": "pop",        "era": "2010s"},

    # ── Pop 2020s (8) ─────────────────────────────────────────────────────
    {"artist": "Harry Styles",          "title": "As It Was",                       "genre": "pop",        "era": "2020s"},
    {"artist": "Olivia Rodrigo",        "title": "drivers license",                 "genre": "pop",        "era": "2020s"},
    {"artist": "Dua Lipa",              "title": "Levitating",                      "genre": "pop",        "era": "2020s"},
    {"artist": "Ariana Grande",         "title": "positions",                       "genre": "pop",        "era": "2020s"},
    {"artist": "The Weeknd",            "title": "Save Your Tears",                 "genre": "pop",        "era": "2020s"},
    {"artist": "Billie Eilish",         "title": "Happier Than Ever",               "genre": "pop",        "era": "2020s"},
    {"artist": "Sam Smith",             "title": "Unholy",                          "genre": "pop",        "era": "2020s"},
    {"artist": "Miley Cyrus",           "title": "Flowers",                         "genre": "pop",        "era": "2020s"},

    # ── Rock 80s (8) ──────────────────────────────────────────────────────
    {"artist": "Guns N' Roses",         "title": "Sweet Child O' Mine",             "genre": "rock",       "era": "80s"},
    {"artist": "Bon Jovi",              "title": "Livin' on a Prayer",              "genre": "rock",       "era": "80s"},
    {"artist": "AC/DC",                 "title": "Back in Black",                   "genre": "rock",       "era": "80s"},
    {"artist": "Journey",               "title": "Don't Stop Believin'",            "genre": "rock",       "era": "80s"},
    {"artist": "The Police",            "title": "Every Breath You Take",           "genre": "rock",       "era": "80s"},
    {"artist": "U2",                    "title": "With or Without You",             "genre": "rock",       "era": "80s"},
    {"artist": "Van Halen",             "title": "Jump",                            "genre": "rock",       "era": "80s"},
    {"artist": "Bruce Springsteen",     "title": "Born in the U.S.A.",              "genre": "rock",       "era": "80s"},

    # ── Rock 90s (10) ─────────────────────────────────────────────────────
    {"artist": "Nirvana",               "title": "Smells Like Teen Spirit",         "genre": "rock",       "era": "90s"},
    {"artist": "Pearl Jam",             "title": "Alive",                           "genre": "rock",       "era": "90s"},
    {"artist": "Foo Fighters",          "title": "Everlong",                        "genre": "rock",       "era": "90s"},
    {"artist": "Green Day",             "title": "Basket Case",                     "genre": "rock",       "era": "90s"},
    {"artist": "Red Hot Chili Peppers", "title": "Under the Bridge",               "genre": "rock",       "era": "90s"},
    {"artist": "Soundgarden",           "title": "Black Hole Sun",                  "genre": "rock",       "era": "90s"},
    {"artist": "Radiohead",             "title": "Creep",                           "genre": "rock",       "era": "90s"},
    {"artist": "Oasis",                 "title": "Wonderwall",                      "genre": "rock",       "era": "90s"},
    {"artist": "Alanis Morissette",     "title": "You Oughta Know",                 "genre": "rock",       "era": "90s"},
    {"artist": "Smashing Pumpkins",     "title": "Bullet with Butterfly Wings",     "genre": "rock",       "era": "90s"},

    # ── Rock 2000s (8) ────────────────────────────────────────────────────
    {"artist": "Linkin Park",           "title": "In the End",                      "genre": "rock",       "era": "2000s"},
    {"artist": "The White Stripes",     "title": "Seven Nation Army",               "genre": "rock",       "era": "2000s"},
    {"artist": "The Killers",           "title": "Mr. Brightside",                  "genre": "rock",       "era": "2000s"},
    {"artist": "Coldplay",              "title": "Yellow",                          "genre": "rock",       "era": "2000s"},
    {"artist": "Snow Patrol",           "title": "Chasing Cars",                    "genre": "rock",       "era": "2000s"},
    {"artist": "Audioslave",            "title": "Like a Stone",                    "genre": "rock",       "era": "2000s"},
    {"artist": "Muse",                  "title": "Time Is Running Out",             "genre": "rock",       "era": "2000s"},
    {"artist": "Kings of Leon",         "title": "Sex on Fire",                     "genre": "rock",       "era": "2000s"},

    # ── Rock 2010s (6) ────────────────────────────────────────────────────
    {"artist": "Imagine Dragons",       "title": "Radioactive",                     "genre": "rock",       "era": "2010s"},
    {"artist": "Twenty One Pilots",     "title": "Stressed Out",                    "genre": "rock",       "era": "2010s"},
    {"artist": "The Black Keys",        "title": "Lonely Boy",                      "genre": "rock",       "era": "2010s"},
    {"artist": "Mumford & Sons",        "title": "I Will Wait",                     "genre": "rock",       "era": "2010s"},
    {"artist": "Royal Blood",           "title": "Figure It Out",                   "genre": "rock",       "era": "2010s"},
    {"artist": "Muse",                  "title": "Madness",                         "genre": "rock",       "era": "2010s"},

    # ── Rock 2020s (4) ────────────────────────────────────────────────────
    {"artist": "Wet Leg",               "title": "Chaise Longue",                   "genre": "rock",       "era": "2020s"},
    {"artist": "Paramore",              "title": "This Is Why",                     "genre": "rock",       "era": "2020s"},
    {"artist": "Fontaines D.C.",        "title": "I Love You",                      "genre": "rock",       "era": "2020s"},
    {"artist": "Inhaler",               "title": "My Honest Face",                  "genre": "rock",       "era": "2020s"},

    # ── Hip-Hop 80s (4) ───────────────────────────────────────────────────
    {"artist": "Run-DMC",               "title": "Walk This Way",                   "genre": "hiphop",     "era": "80s"},
    {"artist": "Beastie Boys",          "title": "Fight for Your Right",            "genre": "hiphop",     "era": "80s"},
    {"artist": "LL Cool J",             "title": "I Need Love",                     "genre": "hiphop",     "era": "80s"},
    {"artist": "N.W.A",                 "title": "Straight Outta Compton",          "genre": "hiphop",     "era": "80s"},

    # ── Hip-Hop 90s (10) ──────────────────────────────────────────────────
    {"artist": "2Pac",                  "title": "California Love",                 "genre": "hiphop",     "era": "90s"},
    {"artist": "The Notorious B.I.G.",  "title": "Juicy",                           "genre": "hiphop",     "era": "90s"},
    {"artist": "Jay-Z",                 "title": "Hard Knock Life",                 "genre": "hiphop",     "era": "90s"},
    {"artist": "Eminem",                "title": "My Name Is",                      "genre": "hiphop",     "era": "90s"},
    {"artist": "Snoop Dogg",            "title": "Gin and Juice",                   "genre": "hiphop",     "era": "90s"},
    {"artist": "Dr. Dre",               "title": "Still D.R.E.",                    "genre": "hiphop",     "era": "90s"},
    {"artist": "Lauryn Hill",           "title": "Doo Wop (That Thing)",            "genre": "hiphop",     "era": "90s"},
    {"artist": "OutKast",               "title": "Ms. Jackson",                     "genre": "hiphop",     "era": "90s"},
    {"artist": "Nas",                   "title": "NY State of Mind",                "genre": "hiphop",     "era": "90s"},
    {"artist": "Wu-Tang Clan",          "title": "C.R.E.A.M.",                      "genre": "hiphop",     "era": "90s"},

    # ── Hip-Hop 2000s (10) ────────────────────────────────────────────────
    {"artist": "Eminem",                "title": "Lose Yourself",                   "genre": "hiphop",     "era": "2000s"},
    {"artist": "50 Cent",               "title": "In Da Club",                      "genre": "hiphop",     "era": "2000s"},
    {"artist": "Kanye West",            "title": "Gold Digger",                     "genre": "hiphop",     "era": "2000s"},
    {"artist": "Lil Wayne",             "title": "Lollipop",                        "genre": "hiphop",     "era": "2000s"},
    {"artist": "Nelly",                 "title": "Hot in Herre",                    "genre": "hiphop",     "era": "2000s"},
    {"artist": "Missy Elliott",         "title": "Work It",                         "genre": "hiphop",     "era": "2000s"},
    {"artist": "Jay-Z",                 "title": "99 Problems",                     "genre": "hiphop",     "era": "2000s"},
    {"artist": "T.I.",                  "title": "Whatever You Like",               "genre": "hiphop",     "era": "2000s"},
    {"artist": "Kanye West",            "title": "Stronger",                        "genre": "hiphop",     "era": "2000s"},
    {"artist": "Drake",                 "title": "Best I Ever Had",                 "genre": "hiphop",     "era": "2000s"},

    # ── Hip-Hop 2010s (10) ────────────────────────────────────────────────
    {"artist": "Drake",                 "title": "God's Plan",                      "genre": "hiphop",     "era": "2010s"},
    {"artist": "Kendrick Lamar",        "title": "HUMBLE.",                         "genre": "hiphop",     "era": "2010s"},
    {"artist": "Cardi B",               "title": "Bodak Yellow",                    "genre": "hiphop",     "era": "2010s"},
    {"artist": "Post Malone",           "title": "Rockstar",                        "genre": "hiphop",     "era": "2010s"},
    {"artist": "Travis Scott",          "title": "Sicko Mode",                      "genre": "hiphop",     "era": "2010s"},
    {"artist": "Nicki Minaj",           "title": "Super Bass",                      "genre": "hiphop",     "era": "2010s"},
    {"artist": "J. Cole",               "title": "No Role Modelz",                  "genre": "hiphop",     "era": "2010s"},
    {"artist": "Childish Gambino",      "title": "This Is America",                 "genre": "hiphop",     "era": "2010s"},
    {"artist": "Migos",                 "title": "Bad and Boujee",                  "genre": "hiphop",     "era": "2010s"},
    {"artist": "Drake",                 "title": "One Dance",                       "genre": "hiphop",     "era": "2010s"},

    # ── Hip-Hop 2020s (8) ─────────────────────────────────────────────────
    {"artist": "Drake",                 "title": "Laugh Now Cry Later",             "genre": "hiphop",     "era": "2020s"},
    {"artist": "Cardi B",               "title": "WAP",                             "genre": "hiphop",     "era": "2020s"},
    {"artist": "Roddy Ricch",           "title": "The Box",                         "genre": "hiphop",     "era": "2020s"},
    {"artist": "Doja Cat",              "title": "Say So",                          "genre": "hiphop",     "era": "2020s"},
    {"artist": "Kendrick Lamar",        "title": "N95",                             "genre": "hiphop",     "era": "2020s"},
    {"artist": "Tyler, the Creator",    "title": "CORSO",                           "genre": "hiphop",     "era": "2020s"},
    {"artist": "Lil Nas X",             "title": "MONTERO (Call Me by Your Name)",  "genre": "hiphop",     "era": "2020s"},
    {"artist": "Jack Harlow",           "title": "First Class",                     "genre": "hiphop",     "era": "2020s"},

    # ── R&B 80s (6) ───────────────────────────────────────────────────────
    {"artist": "Prince",                "title": "Purple Rain",                     "genre": "rb",         "era": "80s"},
    {"artist": "Whitney Houston",       "title": "Greatest Love of All",            "genre": "rb",         "era": "80s"},
    {"artist": "Michael Jackson",       "title": "P.Y.T. (Pretty Young Thing)",     "genre": "rb",         "era": "80s"},
    {"artist": "Janet Jackson",         "title": "Control",                         "genre": "rb",         "era": "80s"},
    {"artist": "Lionel Richie",         "title": "Say You, Say Me",                 "genre": "rb",         "era": "80s"},
    {"artist": "Stevie Wonder",         "title": "I Just Called to Say I Love You", "genre": "rb",         "era": "80s"},

    # ── R&B 90s (8) ───────────────────────────────────────────────────────
    {"artist": "Whitney Houston",       "title": "I Will Always Love You",          "genre": "rb",         "era": "90s"},
    {"artist": "Boyz II Men",           "title": "End of the Road",                 "genre": "rb",         "era": "90s"},
    {"artist": "TLC",                   "title": "Waterfalls",                      "genre": "rb",         "era": "90s"},
    {"artist": "Usher",                 "title": "Nice & Slow",                     "genre": "rb",         "era": "90s"},
    {"artist": "Mariah Carey",          "title": "Always Be My Baby",               "genre": "rb",         "era": "90s"},
    {"artist": "SWV",                   "title": "Weak",                            "genre": "rb",         "era": "90s"},
    {"artist": "En Vogue",              "title": "Don't Let Go (Love)",             "genre": "rb",         "era": "90s"},
    {"artist": "Brian McKnight",        "title": "Back at One",                     "genre": "rb",         "era": "90s"},

    # ── R&B 2000s (8) ─────────────────────────────────────────────────────
    {"artist": "Usher",                 "title": "Yeah!",                           "genre": "rb",         "era": "2000s"},
    {"artist": "Beyoncé",               "title": "Irreplaceable",                   "genre": "rb",         "era": "2000s"},
    {"artist": "Alicia Keys",           "title": "Fallin'",                         "genre": "rb",         "era": "2000s"},
    {"artist": "John Legend",           "title": "Ordinary People",                 "genre": "rb",         "era": "2000s"},
    {"artist": "Mary J. Blige",         "title": "Be Without You",                  "genre": "rb",         "era": "2000s"},
    {"artist": "Ne-Yo",                 "title": "So Sick",                         "genre": "rb",         "era": "2000s"},
    {"artist": "Ciara",                 "title": "Goodies",                         "genre": "rb",         "era": "2000s"},
    {"artist": "Chris Brown",           "title": "With You",                        "genre": "rb",         "era": "2000s"},

    # ── R&B 2010s (8) ─────────────────────────────────────────────────────
    {"artist": "Frank Ocean",           "title": "Thinkin Bout You",                "genre": "rb",         "era": "2010s"},
    {"artist": "The Weeknd",            "title": "Can't Feel My Face",              "genre": "rb",         "era": "2010s"},
    {"artist": "Bryson Tiller",         "title": "Exchange",                        "genre": "rb",         "era": "2010s"},
    {"artist": "H.E.R.",                "title": "Focus",                           "genre": "rb",         "era": "2010s"},
    {"artist": "SZA",                   "title": "Love Galore",                     "genre": "rb",         "era": "2010s"},
    {"artist": "Miguel",                "title": "Adorn",                           "genre": "rb",         "era": "2010s"},
    {"artist": "Rihanna",               "title": "We Found Love",                   "genre": "rb",         "era": "2010s"},
    {"artist": "Alicia Keys",           "title": "Girl on Fire",                    "genre": "rb",         "era": "2010s"},

    # ── R&B 2020s (6) ─────────────────────────────────────────────────────
    {"artist": "Giveon",                "title": "Heartbreak Anniversary",          "genre": "rb",         "era": "2020s"},
    {"artist": "SZA",                   "title": "Good Days",                       "genre": "rb",         "era": "2020s"},
    {"artist": "Silk Sonic",            "title": "Leave the Door Open",             "genre": "rb",         "era": "2020s"},
    {"artist": "Jazmine Sullivan",      "title": "Pick Up Your Feelings",           "genre": "rb",         "era": "2020s"},
    {"artist": "Brent Faiyaz",          "title": "Wasting Time",                    "genre": "rb",         "era": "2020s"},
    {"artist": "Lucky Daye",            "title": "Over",                            "genre": "rb",         "era": "2020s"},

    # ── Electronic 80s (6) ────────────────────────────────────────────────
    {"artist": "Depeche Mode",          "title": "Just Can't Get Enough",           "genre": "electronic", "era": "80s"},
    {"artist": "New Order",             "title": "Blue Monday",                     "genre": "electronic", "era": "80s"},
    {"artist": "The Human League",      "title": "Don't You Want Me",               "genre": "electronic", "era": "80s"},
    {"artist": "Kraftwerk",             "title": "The Model",                       "genre": "electronic", "era": "80s"},
    {"artist": "Eurythmics",            "title": "Sweet Dreams (Are Made of This)", "genre": "electronic", "era": "80s"},
    {"artist": "Pet Shop Boys",         "title": "West End Girls",                  "genre": "electronic", "era": "80s"},

    # ── Electronic 90s (6) ────────────────────────────────────────────────
    {"artist": "The Prodigy",           "title": "Firestarter",                     "genre": "electronic", "era": "90s"},
    {"artist": "Daft Punk",             "title": "Da Funk",                         "genre": "electronic", "era": "90s"},
    {"artist": "Faithless",             "title": "Insomnia",                        "genre": "electronic", "era": "90s"},
    {"artist": "The Chemical Brothers", "title": "Block Rockin' Beats",             "genre": "electronic", "era": "90s"},
    {"artist": "Underworld",            "title": "Born Slippy",                     "genre": "electronic", "era": "90s"},
    {"artist": "Moby",                  "title": "Natural Blues",                   "genre": "electronic", "era": "90s"},

    # ── Electronic 2000s (8) ──────────────────────────────────────────────
    {"artist": "Daft Punk",             "title": "One More Time",                   "genre": "electronic", "era": "2000s"},
    {"artist": "Daft Punk",             "title": "Harder, Better, Faster, Stronger","genre": "electronic", "era": "2000s"},
    {"artist": "The Chemical Brothers", "title": "Galvanize",                       "genre": "electronic", "era": "2000s"},
    {"artist": "Justice",               "title": "D.A.N.C.E.",                      "genre": "electronic", "era": "2000s"},
    {"artist": "Gorillaz",              "title": "DARE",                            "genre": "electronic", "era": "2000s"},
    {"artist": "MGMT",                  "title": "Electric Feel",                   "genre": "electronic", "era": "2000s"},
    {"artist": "Basement Jaxx",         "title": "Where's Your Head At",            "genre": "electronic", "era": "2000s"},
    {"artist": "Röyksopp",              "title": "Remind Me",                       "genre": "electronic", "era": "2000s"},

    # ── Electronic 2010s (8) ──────────────────────────────────────────────
    {"artist": "Avicii",                "title": "Wake Me Up",                      "genre": "electronic", "era": "2010s"},
    {"artist": "Skrillex",              "title": "Bangarang",                       "genre": "electronic", "era": "2010s"},
    {"artist": "Disclosure",            "title": "Latch",                           "genre": "electronic", "era": "2010s"},
    {"artist": "Kygo",                  "title": "Firestone",                       "genre": "electronic", "era": "2010s"},
    {"artist": "Martin Garrix",         "title": "Animals",                         "genre": "electronic", "era": "2010s"},
    {"artist": "Daft Punk",             "title": "Get Lucky",                       "genre": "electronic", "era": "2010s"},
    {"artist": "Flume",                 "title": "Never Be Like You",               "genre": "electronic", "era": "2010s"},
    {"artist": "Swedish House Mafia",   "title": "Don't You Worry Child",           "genre": "electronic", "era": "2010s"},

    # ── Electronic 2020s (6) ──────────────────────────────────────────────
    {"artist": "Dua Lipa",              "title": "Physical",                        "genre": "electronic", "era": "2020s"},
    {"artist": "Glass Animals",         "title": "Heat Waves",                      "genre": "electronic", "era": "2020s"},
    {"artist": "The Kid LAROI",         "title": "Without You",                     "genre": "electronic", "era": "2020s"},
    {"artist": "Tiësto",                "title": "The Business",                    "genre": "electronic", "era": "2020s"},
    {"artist": "Fred again..",          "title": "Delilah (pull me out to the floor)", "genre": "electronic", "era": "2020s"},
    {"artist": "Four Tet",              "title": "Baby",                            "genre": "electronic", "era": "2020s"},

    # ── Metal 80s (6) ─────────────────────────────────────────────────────
    {"artist": "Metallica",             "title": "Master of Puppets",               "genre": "metal",      "era": "80s"},
    {"artist": "Iron Maiden",           "title": "The Trooper",                     "genre": "metal",      "era": "80s"},
    {"artist": "Judas Priest",          "title": "Breaking the Law",                "genre": "metal",      "era": "80s"},
    {"artist": "Ozzy Osbourne",         "title": "Crazy Train",                     "genre": "metal",      "era": "80s"},
    {"artist": "Slayer",                "title": "Raining Blood",                   "genre": "metal",      "era": "80s"},
    {"artist": "Megadeth",              "title": "Peace Sells",                     "genre": "metal",      "era": "80s"},

    # ── Metal 90s (8) ─────────────────────────────────────────────────────
    {"artist": "Metallica",             "title": "Enter Sandman",                   "genre": "metal",      "era": "90s"},
    {"artist": "Pantera",               "title": "Walk",                            "genre": "metal",      "era": "90s"},
    {"artist": "System of a Down",      "title": "Sugar",                           "genre": "metal",      "era": "90s"},
    {"artist": "Marilyn Manson",        "title": "The Beautiful People",            "genre": "metal",      "era": "90s"},
    {"artist": "Tool",                  "title": "Sober",                           "genre": "metal",      "era": "90s"},
    {"artist": "Sepultura",             "title": "Roots Bloody Roots",              "genre": "metal",      "era": "90s"},
    {"artist": "Rage Against the Machine", "title": "Killing in the Name",         "genre": "metal",      "era": "90s"},
    {"artist": "Nine Inch Nails",       "title": "Closer",                          "genre": "metal",      "era": "90s"},

    # ── Metal 2000s (6) ───────────────────────────────────────────────────
    {"artist": "Slipknot",              "title": "Before I Forget",                 "genre": "metal",      "era": "2000s"},
    {"artist": "System of a Down",      "title": "Chop Suey!",                      "genre": "metal",      "era": "2000s"},
    {"artist": "Linkin Park",           "title": "Numb",                            "genre": "metal",      "era": "2000s"},
    {"artist": "Evanescence",           "title": "Bring Me to Life",                "genre": "metal",      "era": "2000s"},
    {"artist": "Disturbed",             "title": "Down with the Sickness",          "genre": "metal",      "era": "2000s"},
    {"artist": "Mastodon",              "title": "Blood and Thunder",               "genre": "metal",      "era": "2000s"},

    # ── Metal 2010s (4) ───────────────────────────────────────────────────
    {"artist": "Ghost",                 "title": "Cirice",                          "genre": "metal",      "era": "2010s"},
    {"artist": "Gojira",                "title": "Silvera",                         "genre": "metal",      "era": "2010s"},
    {"artist": "Trivium",               "title": "In Waves",                        "genre": "metal",      "era": "2010s"},
    {"artist": "Parkway Drive",         "title": "Wild Eyes",                       "genre": "metal",      "era": "2010s"},

    # ── Metal 2020s (2) ───────────────────────────────────────────────────
    {"artist": "Spiritbox",             "title": "Holy Roller",                     "genre": "metal",      "era": "2020s"},
    {"artist": "Sleep Token",           "title": "The Summoning",                   "genre": "metal",      "era": "2020s"},

    # ── Indie 80s (4) ─────────────────────────────────────────────────────
    {"artist": "The Smiths",            "title": "There Is a Light That Never Goes Out", "genre": "indie", "era": "80s"},
    {"artist": "The Cure",              "title": "Lovesong",                        "genre": "indie",      "era": "80s"},
    {"artist": "Pixies",                "title": "Where Is My Mind?",               "genre": "indie",      "era": "80s"},
    {"artist": "Talking Heads",         "title": "Once in a Lifetime",              "genre": "indie",      "era": "80s"},

    # ── Indie 90s (6) ─────────────────────────────────────────────────────
    {"artist": "R.E.M.",                "title": "Losing My Religion",              "genre": "indie",      "era": "90s"},
    {"artist": "Beck",                  "title": "Loser",                           "genre": "indie",      "era": "90s"},
    {"artist": "Blur",                  "title": "Song 2",                          "genre": "indie",      "era": "90s"},
    {"artist": "Weezer",                "title": "Buddy Holly",                     "genre": "indie",      "era": "90s"},
    {"artist": "Counting Crows",        "title": "Mr. Jones",                       "genre": "indie",      "era": "90s"},
    {"artist": "The Cranberries",       "title": "Zombie",                          "genre": "indie",      "era": "90s"},

    # ── Indie 2000s (6) ───────────────────────────────────────────────────
    {"artist": "The Strokes",           "title": "Last Nite",                       "genre": "indie",      "era": "2000s"},
    {"artist": "Franz Ferdinand",       "title": "Take Me Out",                     "genre": "indie",      "era": "2000s"},
    {"artist": "Arcade Fire",           "title": "Rebellion (Lies)",                "genre": "indie",      "era": "2000s"},
    {"artist": "Interpol",              "title": "Obstacle 1",                      "genre": "indie",      "era": "2000s"},
    {"artist": "Death Cab for Cutie",   "title": "Soul Meets Body",                 "genre": "indie",      "era": "2000s"},
    {"artist": "Modest Mouse",          "title": "Float On",                        "genre": "indie",      "era": "2000s"},

    # ── Indie 2010s (8) ───────────────────────────────────────────────────
    {"artist": "Tame Impala",           "title": "Elephant",                        "genre": "indie",      "era": "2010s"},
    {"artist": "Vampire Weekend",       "title": "Diane Young",                     "genre": "indie",      "era": "2010s"},
    {"artist": "The Lumineers",         "title": "Ho Hey",                          "genre": "indie",      "era": "2010s"},
    {"artist": "Of Monsters and Men",   "title": "Little Talks",                    "genre": "indie",      "era": "2010s"},
    {"artist": "Alt-J",                 "title": "Something Good",                  "genre": "indie",      "era": "2010s"},
    {"artist": "The 1975",              "title": "Chocolate",                       "genre": "indie",      "era": "2010s"},
    {"artist": "Mac DeMarco",           "title": "Salad Days",                      "genre": "indie",      "era": "2010s"},
    {"artist": "Arctic Monkeys",        "title": "R U Mine?",                       "genre": "indie",      "era": "2010s"},

    # ── Indie 2020s (6) ───────────────────────────────────────────────────
    {"artist": "Phoebe Bridgers",       "title": "Garden Song",                     "genre": "indie",      "era": "2020s"},
    {"artist": "Clairo",                "title": "Amoeba",                          "genre": "indie",      "era": "2020s"},
    {"artist": "Mitski",                "title": "The Only Heartbreaker",           "genre": "indie",      "era": "2020s"},
    {"artist": "Japanese Breakfast",    "title": "Paprika",                         "genre": "indie",      "era": "2020s"},
    {"artist": "Big Thief",             "title": "Not",                             "genre": "indie",      "era": "2020s"},
    {"artist": "boygenius",             "title": "$20",                             "genre": "indie",      "era": "2020s"},

    # ── Latin 80s (2) ─────────────────────────────────────────────────────
    {"artist": "Gloria Estefan",        "title": "Get On Your Feet",                "genre": "latin",      "era": "80s"},
    {"artist": "Julio Iglesias",        "title": "To All the Girls I've Loved Before", "genre": "latin",   "era": "80s"},

    # ── Latin 90s (4) ─────────────────────────────────────────────────────
    {"artist": "Ricky Martin",          "title": "Livin' la Vida Loca",             "genre": "latin",      "era": "90s"},
    {"artist": "Marc Anthony",          "title": "I Need to Know",                  "genre": "latin",      "era": "90s"},
    {"artist": "Jennifer Lopez",        "title": "If You Had My Love",              "genre": "latin",      "era": "90s"},
    {"artist": "Gloria Estefan",        "title": "Coming Out of the Dark",          "genre": "latin",      "era": "90s"},

    # ── Latin 2000s (6) ───────────────────────────────────────────────────
    {"artist": "Shakira",               "title": "Whenever, Wherever",              "genre": "latin",      "era": "2000s"},
    {"artist": "Daddy Yankee",          "title": "Gasolina",                        "genre": "latin",      "era": "2000s"},
    {"artist": "Enrique Iglesias",      "title": "Hero",                            "genre": "latin",      "era": "2000s"},
    {"artist": "Jennifer Lopez",        "title": "Jenny from the Block",            "genre": "latin",      "era": "2000s"},
    {"artist": "Ricky Martin",          "title": "She Bangs",                       "genre": "latin",      "era": "2000s"},
    {"artist": "Marc Anthony",          "title": "Ahora Quién",                     "genre": "latin",      "era": "2000s"},

    # ── Latin 2010s (8) ───────────────────────────────────────────────────
    {"artist": "Luis Fonsi",            "title": "Despacito",                       "genre": "latin",      "era": "2010s"},
    {"artist": "J Balvin",              "title": "Mi Gente",                        "genre": "latin",      "era": "2010s"},
    {"artist": "Maluma",                "title": "Felices los 4",                   "genre": "latin",      "era": "2010s"},
    {"artist": "Bad Bunny",             "title": "Soy Peor",                        "genre": "latin",      "era": "2010s"},
    {"artist": "Becky G",               "title": "Mayores",                         "genre": "latin",      "era": "2010s"},
    {"artist": "Ozuna",                 "title": "El Farsante",                     "genre": "latin",      "era": "2010s"},
    {"artist": "CNCO",                  "title": "Reggaetón Lento",                 "genre": "latin",      "era": "2010s"},
    {"artist": "Nicky Jam",             "title": "El Perdón",                       "genre": "latin",      "era": "2010s"},

    # ── Latin 2020s (8) ───────────────────────────────────────────────────
    {"artist": "Bad Bunny",             "title": "Dakiti",                          "genre": "latin",      "era": "2020s"},
    {"artist": "Maluma",                "title": "Hawái",                           "genre": "latin",      "era": "2020s"},
    {"artist": "Rauw Alejandro",        "title": "Todo De Ti",                      "genre": "latin",      "era": "2020s"},
    {"artist": "Karol G",               "title": "BICHOTA",                         "genre": "latin",      "era": "2020s"},
    {"artist": "Bad Bunny",             "title": "Tití Me Preguntó",                "genre": "latin",      "era": "2020s"},
    {"artist": "Shakira",               "title": "BZRP Music Sessions, Vol. 53",    "genre": "latin",      "era": "2020s"},
    {"artist": "Rosalía",               "title": "La Fama",                         "genre": "latin",      "era": "2020s"},
    {"artist": "Grupo Frontera",        "title": "No Se Va",                        "genre": "latin",      "era": "2020s"},

    # ── K-Pop 90s (2) ─────────────────────────────────────────────────────
    {"artist": "H.O.T.",                "title": "Candy",                           "genre": "kpop",       "era": "90s"},
    {"artist": "S.E.S.",                "title": "I'm Your Girl",                   "genre": "kpop",       "era": "90s"},

    # ── K-Pop 2000s (4) ───────────────────────────────────────────────────
    {"artist": "BoA",                   "title": "Listen to My Heart",              "genre": "kpop",       "era": "2000s"},
    {"artist": "TVXQ",                  "title": "Rising Sun",                      "genre": "kpop",       "era": "2000s"},
    {"artist": "Wonder Girls",          "title": "Nobody",                          "genre": "kpop",       "era": "2000s"},
    {"artist": "Girls' Generation",     "title": "Gee",                             "genre": "kpop",       "era": "2000s"},

    # ── K-Pop 2010s (9) ───────────────────────────────────────────────────
    {"artist": "PSY",                   "title": "Gangnam Style",                   "genre": "kpop",       "era": "2010s"},
    {"artist": "BTS",                   "title": "DNA",                             "genre": "kpop",       "era": "2010s"},
    {"artist": "BLACKPINK",             "title": "DDU-DU DDU-DU",                   "genre": "kpop",       "era": "2010s"},
    {"artist": "EXO",                   "title": "Growl",                           "genre": "kpop",       "era": "2010s"},
    {"artist": "TWICE",                 "title": "TT",                              "genre": "kpop",       "era": "2010s"},
    {"artist": "Red Velvet",            "title": "Red Flavor",                      "genre": "kpop",       "era": "2010s"},
    {"artist": "SHINee",                "title": "View",                            "genre": "kpop",       "era": "2010s"},
    {"artist": "GOT7",                  "title": "Hard Carry",                      "genre": "kpop",       "era": "2010s"},
    {"artist": "MONSTA X",              "title": "Hero",                            "genre": "kpop",       "era": "2010s"},

    # ── K-Pop 2020s (8) ───────────────────────────────────────────────────
    {"artist": "BTS",                   "title": "Dynamite",                        "genre": "kpop",       "era": "2020s"},
    {"artist": "BLACKPINK",             "title": "How You Like That",               "genre": "kpop",       "era": "2020s"},
    {"artist": "aespa",                 "title": "Next Level",                      "genre": "kpop",       "era": "2020s"},
    {"artist": "Stray Kids",            "title": "MIROH",                           "genre": "kpop",       "era": "2020s"},
    {"artist": "ITZY",                  "title": "DALLA DALLA",                     "genre": "kpop",       "era": "2020s"},
    {"artist": "NewJeans",              "title": "Hype Boy",                        "genre": "kpop",       "era": "2020s"},
    {"artist": "IVE",                   "title": "LOVE DIVE",                       "genre": "kpop",       "era": "2020s"},
    {"artist": "LE SSERAFIM",           "title": "ANTIFRAGILE",                     "genre": "kpop",       "era": "2020s"},
]


# ── Game config ────────────────────────────────────────────────────────────


@dataclass
class GameConfig:
    # ── Round settings ─────────────────────────────────────────────────────
    round_timeout_seconds: int = 10
    clip_duration_seconds: int = 8

    # ── Scoring ────────────────────────────────────────────────────────────
    points_correct_title:  int = 100
    points_correct_artist: int = 50

    # ── Game mode ──────────────────────────────────────────────────────────
    choices_count: int = 4

    # ── Matching (free_text mode only) ─────────────────────────────────────
    partial_match_enabled:    bool  = True
    partial_match_threshold:  float = 0.6

    def apply_difficulty(self, difficulty: str = "normal") -> None:
        if difficulty == "easy":
            self.clip_duration_seconds = 15
            self.round_timeout_seconds = 20
            self.partial_match_enabled = True
        elif difficulty == "hard":
            self.clip_duration_seconds = 3
            self.round_timeout_seconds = 7
            self.partial_match_enabled = False
        else:
            self.clip_duration_seconds = 8
            self.round_timeout_seconds = 10
            self.partial_match_enabled = True
