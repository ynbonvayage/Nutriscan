"""
Local nutrition database for all 256 UEC FOOD-256 categories.

No external API or network calls required.

Public API
----------
get_nutrition(food_name) -> dict
    Returns {calories, protein_g, carbs_g, fat_g, serving_g, serving_desc}
    for the best-matching food. Falls back to zeroes on no match.

aggregate(food_list) -> dict
    Sums nutrients across a list of food name strings.
"""

# ---------------------------------------------------------------------------
# Database
# Each entry: (calories, protein_g, carbs_g, fat_g, serving_g, serving_desc)
# Macros are per the listed serving.  Sources: USDA FoodData Central,
# Japanese Standard Tables of Food Composition (8th ed.), and
# standard culinary references.
# ---------------------------------------------------------------------------

_DB: dict[str, tuple] = {

    # ── Rice dishes ──────────────────────────────────────────────────────────
    "rice":                       (195,  4.0,  43.0,  0.4, 150, "150 g cooked"),
    "eels on rice":               (500, 27.0,  66.0, 14.0, 300, "1 bowl"),
    "pilaf":                      (320, 10.0,  52.0,  8.0, 200, "1 serving"),
    "chicken-n-egg on rice":      (520, 28.0,  68.0, 12.0, 350, "1 bowl"),
    "pork cutlet on rice":        (650, 30.0,  72.0, 22.0, 380, "1 bowl"),
    "beef curry":                 (580, 22.0,  70.0, 20.0, 380, "1 plate"),
    "sushi":                      (380, 18.0,  58.0,  8.0, 240, "8 pieces"),
    "chicken rice":               (420, 20.0,  62.0,  8.0, 280, "1 serving"),
    "fried rice":                 (450, 14.0,  62.0, 14.0, 260, "1 serving"),
    "gyudon":                     (580, 28.0,  68.0, 18.0, 380, "1 bowl"),
    "oyakodon":                   (520, 28.0,  68.0, 12.0, 350, "1 bowl"),
    "katsudon":                   (650, 30.0,  72.0, 22.0, 380, "1 bowl"),
    "tendon":                     (560, 22.0,  76.0, 16.0, 360, "1 bowl"),
    "unadon":                     (500, 27.0,  66.0, 14.0, 300, "1 bowl"),
    "tekkadon":                   (430, 24.0,  62.0,  8.0, 300, "1 bowl"),
    "chirashi sushi":             (440, 22.0,  66.0, 10.0, 320, "1 bowl"),
    "inari sushi":                (320, 10.0,  56.0,  6.0, 200, "4 pieces"),
    "nigiri sushi":               (360, 16.0,  54.0,  8.0, 240, "8 pieces"),
    "temaki sushi":               (280, 14.0,  40.0,  7.0, 200, "2 rolls"),
    "onigiri":                    (180,  4.0,  38.0,  1.0, 100, "1 rice ball"),
    "chahan":                     (420, 12.0,  62.0, 12.0, 260, "1 serving"),
    "bibimbap":                   (490, 18.0,  72.0, 12.0, 380, "1 bowl"),
    "congee":                     (120,  4.0,  24.0,  1.0, 250, "1 bowl"),
    "risotto":                    (380, 12.0,  56.0, 12.0, 280, "1 serving"),
    "paella":                     (480, 24.0,  56.0, 16.0, 320, "1 serving"),
    "biryani":                    (520, 22.0,  68.0, 16.0, 340, "1 serving"),

    # ── Breads & sandwiches ──────────────────────────────────────────────────
    "white bread":                (160,  6.0,  30.0,  2.0,  60, "2 slices"),
    "roll bread":                 (200,  6.0,  32.0,  5.0,  70, "2 rolls"),
    "croissant":                  (240,  5.0,  28.0, 12.0,  60, "1 medium"),
    "french bread":               (220,  7.0,  43.0,  2.0,  80, "2 slices"),
    "stick bread":                (220,  7.0,  43.0,  1.0,  80, "1/4 baguette"),
    "toast":                      (180,  7.0,  32.0,  3.0,  70, "2 slices"),
    "sandwiches":                 (380, 18.0,  38.0, 14.0, 200, "1 sandwich"),
    "club sandwich":              (440, 22.0,  42.0, 18.0, 230, "1 sandwich"),
    "tonkatsu sandwich":          (480, 22.0,  48.0, 20.0, 240, "1 sandwich"),
    "BLT sandwich":               (380, 18.0,  36.0, 16.0, 200, "1 sandwich"),
    "tuna sandwich":              (340, 20.0,  34.0, 12.0, 190, "1 sandwich"),
    "egg salad sandwich":         (320, 14.0,  32.0, 14.0, 190, "1 sandwich"),
    "grilled cheese":             (400, 16.0,  36.0, 22.0, 200, "1 sandwich"),
    "Reuben sandwich":            (520, 28.0,  44.0, 24.0, 270, "1 sandwich"),
    "pulled pork sandwich":       (540, 30.0,  46.0, 22.0, 280, "1 sandwich"),
    "fried chicken sandwich":     (450, 24.0,  42.0, 20.0, 240, "1 sandwich"),
    "hamburger":                  (540, 28.0,  40.0, 28.0, 250, "1 burger"),
    "beef burger":                (540, 28.0,  40.0, 28.0, 250, "1 burger"),
    "cheeseburger":               (590, 30.0,  42.0, 32.0, 260, "1 burger"),
    "turkey burger":              (400, 28.0,  38.0, 14.0, 220, "1 burger"),
    "veggie burger":              (360, 16.0,  42.0, 12.0, 200, "1 burger"),
    "pizza":                      (500, 22.0,  56.0, 18.0, 200, "2 slices"),
    "hot dog":                    (290, 12.0,  22.0, 16.0, 130, "1 hot dog"),
    "corn dog":                   (340, 12.0,  36.0, 16.0, 150, "1 corn dog"),
    "pita bread":                 (280,  9.0,  56.0,  2.0, 120, "2 pitas"),
    "naan":                       (320, 10.0,  56.0,  7.0, 130, "1 piece"),
    "tortilla":                   (300,  8.0,  52.0,  7.0, 120, "2 tortillas"),

    # ── Noodles ──────────────────────────────────────────────────────────────
    "ramen":                      (450, 22.0,  58.0, 14.0, 400, "1 bowl"),
    "shoyu ramen":                (430, 22.0,  56.0, 12.0, 400, "1 bowl"),
    "miso ramen":                 (470, 22.0,  58.0, 16.0, 400, "1 bowl"),
    "shio ramen":                 (400, 20.0,  54.0, 10.0, 400, "1 bowl"),
    "tonkotsu ramen":             (510, 24.0,  58.0, 20.0, 400, "1 bowl"),
    "tan-men":                    (390, 16.0,  56.0, 10.0, 400, "1 bowl"),
    "tsukemen":                   (580, 28.0,  72.0, 16.0, 450, "1 serving"),
    "hiyashi chuka":              (380, 14.0,  58.0, 10.0, 320, "1 serving"),
    "mazesoba":                   (520, 24.0,  64.0, 18.0, 380, "1 bowl"),
    "tantanmen":                  (500, 22.0,  56.0, 20.0, 400, "1 bowl"),
    "udon":                       (310, 10.0,  62.0,  1.5, 350, "1 bowl"),
    "kitsune udon":               (360, 14.0,  66.0,  6.0, 380, "1 bowl"),
    "tempura udon":               (490, 18.0,  72.0, 14.0, 420, "1 bowl"),
    "soba":                       (340, 13.0,  67.0,  1.8, 350, "1 bowl"),
    "zaru soba":                  (320, 12.0,  62.0,  1.5, 300, "1 serving"),
    "yakisoba":                   (420, 14.0,  58.0, 14.0, 300, "1 serving"),
    "yakisoba pan":               (420, 14.0,  64.0, 10.0, 280, "1 bread roll"),
    "fried noodles":              (380, 12.0,  52.0, 12.0, 280, "1 serving"),
    "rice noodles":               (350,  8.0,  68.0,  4.0, 280, "1 serving"),
    "cold noodles":               (320, 10.0,  60.0,  4.0, 280, "1 serving"),
    "Chinese noodles":            (360, 12.0,  56.0,  8.0, 300, "1 serving"),
    "spaghetti":                  (420, 16.0,  62.0, 12.0, 280, "1 serving"),
    "carbonara":                  (520, 20.0,  54.0, 24.0, 300, "1 serving"),
    "aglio olio":                 (420, 12.0,  60.0, 14.0, 280, "1 serving"),
    "penne arrabiata":            (380, 12.0,  62.0,  9.0, 280, "1 serving"),
    "fettuccine":                 (440, 16.0,  58.0, 16.0, 300, "1 serving"),
    "lasagna":                    (400, 20.0,  38.0, 18.0, 280, "1 serving"),
    "ravioli":                    (350, 14.0,  48.0, 12.0, 250, "1 serving"),
    "macaroni":                   (350, 12.0,  58.0,  8.0, 220, "1 serving"),
    "pad thai":                   (380, 16.0,  54.0, 12.0, 300, "1 serving"),
    "pho":                        (420, 26.0,  58.0,  8.0, 450, "1 bowl"),

    # ── Soups & stews ────────────────────────────────────────────────────────
    "miso soup":                  ( 40,  3.0,   4.8,  1.5, 200, "1 bowl"),
    "potage":                     (120,  3.0,  18.0,  4.0, 200, "1 bowl"),
    "stew":                       (280, 18.0,  22.0, 12.0, 300, "1 bowl"),
    "curry":                      (520, 20.0,  66.0, 18.0, 380, "1 plate"),
    "beef curry":                 (580, 22.0,  70.0, 20.0, 380, "1 plate"),
    "chicken curry":              (450, 26.0,  38.0, 18.0, 350, "1 plate"),
    "pork curry":                 (480, 24.0,  40.0, 22.0, 350, "1 plate"),
    "Japanese curry":             (520, 20.0,  66.0, 18.0, 380, "1 plate"),
    "green curry":                (420, 22.0,  24.0, 28.0, 300, "1 bowl"),
    "tom yum":                    (150, 12.0,  10.0,  6.0, 300, "1 bowl"),
    "clam chowder":               (240, 10.0,  26.0, 12.0, 280, "1 bowl"),
    "french onion soup":          (220,  8.0,  22.0, 10.0, 280, "1 bowl"),
    "minestrone":                 (160,  7.0,  24.0,  4.0, 280, "1 bowl"),
    "tomato soup":                (140,  3.0,  20.0,  5.0, 240, "1 bowl"),
    "corn soup":                  (180,  5.0,  26.0,  6.0, 240, "1 bowl"),
    "pumpkin soup":               (150,  3.0,  22.0,  5.0, 240, "1 bowl"),
    "gazpacho":                   ( 80,  2.0,  14.0,  2.0, 240, "1 bowl"),
    "borscht":                    (130,  4.0,  18.0,  5.0, 280, "1 bowl"),
    "gratin":                     (380, 16.0,  32.0, 20.0, 280, "1 serving"),
    "oden":                       (200, 12.0,  20.0,  6.0, 300, "1 serving"),

    # ── Salads ───────────────────────────────────────────────────────────────
    "salad":                      (120,  3.0,  12.0,  6.0, 150, "1 serving"),
    "Japanese salad":             ( 90,  2.0,  10.0,  4.0, 150, "1 serving"),
    "Caesar salad":               (220,  8.0,  14.0, 16.0, 200, "1 serving"),
    "Greek salad":                (150,  5.0,  12.0, 10.0, 200, "1 serving"),
    "Caprese salad":              (200, 10.0,   6.0, 16.0, 200, "1 serving"),
    "Waldorf salad":              (180,  4.0,  16.0, 12.0, 200, "1 serving"),
    "coleslaw":                   (120,  1.5,  14.0,  7.0, 150, "1 serving"),
    "potato salad":               (200,  4.0,  24.0, 10.0, 200, "1 serving"),
    "egg salad":                  (180, 10.0,   4.0, 14.0, 150, "1 serving"),
    "tuna salad":                 (190, 20.0,   4.0, 10.0, 150, "1 serving"),
    "Nicoise salad":              (230, 18.0,  14.0, 12.0, 250, "1 serving"),
    "fruit salad":                ( 80,  1.0,  20.0,  0.3, 150, "1 serving"),
    "mixed green salad":          ( 50,  2.0,   6.0,  2.0, 100, "1 serving"),
    "green papaya salad":         ( 60,  2.0,  10.0,  1.0, 150, "1 serving"),

    # ── Seafood dishes ───────────────────────────────────────────────────────
    "sea bream":                  (140, 22.0,   0.0,  5.0, 100, "100 g"),
    "salmon":                     (208, 28.0,   0.0, 10.0, 100, "100 g"),
    "tuna":                       (130, 28.0,   0.0,  1.0, 100, "100 g"),
    "squid":                      ( 92, 16.0,   3.0,  1.4, 100, "100 g"),
    "shrimp":                     ( 99, 19.0,   0.9,  1.5, 100, "100 g"),
    "crab":                       ( 97, 20.0,   0.0,  1.5, 100, "100 g"),
    "octopus":                    ( 82, 15.0,   2.2,  1.0, 100, "100 g"),
    "clam":                       ( 74, 13.0,   3.0,  1.0, 100, "100 g"),
    "oysters":                    ( 80,  9.0,   4.7,  2.5, 100, "100 g"),
    "scallop":                    (111, 23.0,   3.0,  0.8, 100, "100 g"),
    "abalone":                    (105, 18.0,   5.0,  1.0, 100, "100 g"),
    "sashimi":                    (160, 24.0,   2.0,  6.0, 120, "1 serving"),
    "grilled fish":               (220, 26.0,   0.0, 12.0, 130, "1 fillet"),
    "grilled salmon":             (260, 28.0,   0.0, 16.0, 130, "1 fillet"),
    "grilled mackerel":           (290, 26.0,   0.0, 20.0, 130, "1 fillet"),
    "grilled saury":              (230, 22.0,   0.0, 16.0, 120, "1 fish"),
    "boiled fish":                (180, 24.0,   2.0,  8.0, 130, "1 serving"),
    "fried shrimp":               (280, 18.0,  22.0, 12.0, 150, "4 pieces"),

    # ── Tofu & soy ──────────────────────────────────────────────────────────
    "tofu":                       ( 94, 10.0,   2.3,  5.0, 150, "1/2 block"),
    "natto":                      (190, 16.0,  11.0, 10.0, 100, "1 pack"),
    "agedashi tofu":              (180, 10.0,  14.0,  9.0, 180, "1 serving"),

    # ── Egg dishes ──────────────────────────────────────────────────────────
    "egg":                        ( 70,  6.0,   0.6,  5.0,  50, "1 large"),
    "omelet":                     (200, 12.0,   4.0, 16.0, 120, "1 omelet"),
    "tamagoyaki":                 (120,  8.0,   6.0,  8.0,  80, "1 serving"),
    "french toast":               (290,  9.0,  38.0, 12.0, 150, "2 slices"),

    # ── Fried & grilled meats ────────────────────────────────────────────────
    "pork cutlet":                (420, 24.0,  28.0, 22.0, 200, "1 cutlet"),
    "tonkatsu":                   (420, 24.0,  28.0, 22.0, 200, "1 cutlet"),
    "fried chicken":              (320, 28.0,  14.0, 16.0, 180, "2 pieces"),
    "chicken karaage":            (320, 28.0,  12.0, 18.0, 180, "4 pieces"),
    "tempura":                    (380, 16.0,  34.0, 20.0, 200, "1 serving"),
    "hamburger steak":            (380, 24.0,  12.0, 26.0, 200, "1 patty"),
    "hambagu":                    (380, 24.0,  12.0, 26.0, 200, "1 patty"),
    "steak":                      (470, 38.0,   0.0, 34.0, 200, "1 steak"),
    "grilled beef":               (350, 32.0,   2.0, 24.0, 180, "1 serving"),
    "yakiniku":                   (380, 28.0,   4.0, 28.0, 180, "1 serving"),
    "sukiyaki":                   (480, 26.0,  32.0, 26.0, 350, "1 serving"),
    "shabu shabu":                (380, 28.0,   8.0, 22.0, 300, "1 serving"),
    "teriyaki chicken":           (320, 30.0,  14.0, 14.0, 200, "1 serving"),
    "yakitori":                   (220, 22.0,   8.0, 10.0, 120, "4 skewers"),
    "roast chicken":              (280, 34.0,   0.0, 16.0, 180, "1 serving"),
    "grilled chicken":            (260, 36.0,   0.0, 12.0, 180, "1 serving"),
    "chicken wings":              (430, 32.0,   4.0, 30.0, 200, "6 wings"),
    "chicken nuggets":            (280, 18.0,  18.0, 14.0, 150, "6 nuggets"),

    # ── Japanese snacks & street food ────────────────────────────────────────
    "gyoza":                      (280, 14.0,  28.0, 12.0, 180, "6 pieces"),
    "shumai":                     (240, 14.0,  22.0, 10.0, 150, "5 pieces"),
    "spring rolls":               (220,  8.0,  24.0, 10.0, 120, "3 rolls"),
    "egg rolls":                  (230,  8.0,  26.0, 10.0, 130, "3 rolls"),
    "okonomiyaki":                (420, 16.0,  44.0, 18.0, 280, "1 pancake"),
    "takoyaki":                   (320, 12.0,  36.0, 14.0, 180, "6 balls"),
    "dango":                      (100,  1.5,  22.0,  0.5,  60, "3 pieces"),
    "mitarashi dango":            (110,  2.0,  24.0,  1.0,  65, "3 pieces"),
    "mochi":                      (100,  1.5,  22.0,  0.5,  60, "1 piece"),
    "daifuku":                    (130,  2.0,  28.0,  1.0,  70, "1 piece"),
    "dorayaki":                   (190,  4.0,  36.0,  4.0,  90, "1 piece"),
    "taiyaki":                    (200,  4.5,  36.0,  5.0, 100, "1 piece"),
    "anmitsu":                    (200,  3.0,  44.0,  1.0, 200, "1 serving"),
    "kakigori":                   (120,  0.5,  30.0,  0.0, 200, "1 serving"),
    "wagashi":                    (150,  2.0,  34.0,  1.0,  70, "2 pieces"),
    "yokan":                      (160,  2.0,  38.0,  0.2,  80, "1 serving"),
    "castella":                   (280,  6.0,  52.0,  6.0, 100, "1 slice"),

    # ── Korean foods ─────────────────────────────────────────────────────────
    "kimchi":                     ( 23,  1.8,   3.6,  0.5, 100, "100 g"),
    "japchae":                    (280,  8.0,  44.0,  8.0, 200, "1 serving"),
    "bulgogi":                    (320, 28.0,  12.0, 18.0, 200, "1 serving"),
    "tteokbokki":                 (340,  8.0,  60.0,  6.0, 250, "1 serving"),

    # ── Chinese & pan-Asian ──────────────────────────────────────────────────
    "dumplings":                  (300, 14.0,  34.0, 12.0, 180, "6 pieces"),
    "baozi":                      (280, 10.0,  44.0,  7.0, 170, "2 buns"),
    "wontons":                    (250, 12.0,  30.0,  8.0, 150, "6 pieces"),
    "dim sum":                    (340, 14.0,  42.0, 12.0, 200, "1 serving"),
    "peking duck":                (440, 30.0,   8.0, 34.0, 200, "1 serving"),
    "mapo tofu":                  (280, 14.0,  12.0, 18.0, 250, "1 serving"),

    # ── Mexican & Tex-Mex ────────────────────────────────────────────────────
    "nachos":                     (480, 12.0,  52.0, 24.0, 200, "1 serving"),
    "tacos":                      (350, 18.0,  32.0, 16.0, 200, "2 tacos"),
    "burritos":                   (520, 22.0,  58.0, 20.0, 300, "1 burrito"),
    "quesadilla":                 (420, 18.0,  38.0, 22.0, 200, "1 serving"),
    "enchiladas":                 (380, 18.0,  40.0, 16.0, 250, "2 enchiladas"),
    "fajitas":                    (380, 22.0,  34.0, 16.0, 230, "1 serving"),
    "guacamole":                  (160,  2.0,  10.0, 14.0, 100, "2 tbsp"),
    "salsa":                      ( 30,  1.0,   6.0,  0.2,  60, "4 tbsp"),

    # ── Snacks & sides ───────────────────────────────────────────────────────
    "french fries":               (380,  4.0,  52.0, 18.0, 150, "medium serving"),
    "onion rings":                (350,  5.0,  42.0, 18.0, 130, "1 serving"),
    "mozzarella sticks":          (420, 18.0,  32.0, 24.0, 150, "4 sticks"),
    "potato chips":               (520,  7.0,  52.0, 32.0, 100, "1 bag"),
    "popcorn":                    (380, 11.0,  76.0,  4.0, 100, "3 cups"),
    "pretzels":                   (380,  9.0,  80.0,  2.0, 100, "1 serving"),
    "crackers":                   (440,  8.0,  72.0, 14.0, 100, "1 serving"),
    "edamame":                    (120, 11.0,  10.0,  5.0, 100, "100 g"),

    # ── Breakfast ────────────────────────────────────────────────────────────
    "waffle":                     (310,  8.0,  42.0, 12.0, 120, "1 large"),
    "pancake":                    (260,  7.0,  38.0,  9.0, 110, "2 medium"),
    "oatmeal":                    (170,  6.0,  28.0,  3.5, 170, "1 bowl"),
    "granola":                    (450, 12.0,  68.0, 16.0, 100, "1 cup"),
    "yogurt":                     (150,  8.0,  18.0,  4.0, 170, "1 cup"),

    # ── Dairy & condiments ───────────────────────────────────────────────────
    "cheese":                     (280, 16.0,   1.3, 24.0,  60, "2 slices"),
    "butter":                     (100,  0.1,   0.0, 11.0,  14, "1 tbsp"),
    "jam":                        ( 50,  0.1,  13.0,  0.0,  20, "1 tbsp"),
    "honey":                      ( 60,  0.0,  17.0,  0.0,  21, "1 tbsp"),

    # ── Desserts & sweets ────────────────────────────────────────────────────
    "chocolate":                  (220,  2.5,  26.0, 13.0,  40, "4 squares"),
    "cake":                       (350,  4.0,  52.0, 16.0, 100, "1 slice"),
    "cheesecake":                 (400,  7.0,  38.0, 26.0, 120, "1 slice"),
    "brownie":                    (340,  4.0,  46.0, 16.0, 100, "1 piece"),
    "cookie":                     (150,  2.0,  20.0,  7.0,  30, "2 cookies"),
    "donut":                      (290,  4.0,  36.0, 14.0,  75, "1 donut"),
    "muffin":                     (340,  5.0,  50.0, 14.0, 110, "1 muffin"),
    "scone":                      (300,  6.0,  42.0, 12.0, 100, "1 scone"),
    "macaron":                    (100,  1.5,  15.0,  4.0,  25, "1 macaron"),
    "eclair":                     (280,  6.0,  30.0, 16.0,  90, "1 eclair"),
    "cream puff":                 (240,  5.0,  26.0, 14.0,  80, "1 puff"),
    "tiramisu":                   (280,  6.0,  30.0, 16.0, 120, "1 serving"),
    "panna cotta":                (220,  4.0,  24.0, 12.0, 120, "1 serving"),
    "creme brulee":               (260,  5.0,  26.0, 16.0, 120, "1 ramekin"),
    "pudding":                    (200,  4.0,  32.0,  7.0, 120, "1 cup"),
    "ice cream":                  (270,  5.0,  32.0, 14.0, 130, "2 scoops"),
    "sorbet":                     (180,  0.5,  46.0,  0.2, 130, "2 scoops"),
    "gelato":                     (230,  4.0,  36.0,  9.0, 130, "2 scoops"),
    "mousse":                     (240,  4.0,  22.0, 16.0, 100, "1 serving"),
    "tart":                       (320,  5.0,  40.0, 16.0, 100, "1 slice"),
    "apple pie":                  (300,  3.0,  44.0, 13.0, 125, "1 slice"),
    "pumpkin pie":                (320,  5.0,  46.0, 13.0, 130, "1 slice"),
    "peach pie":                  (300,  3.0,  44.0, 13.0, 125, "1 slice"),
    "cherry pie":                 (310,  3.0,  46.0, 13.0, 125, "1 slice"),
    "lemon tart":                 (290,  5.0,  38.0, 14.0, 110, "1 slice"),
    "strawberry shortcake":       (290,  4.0,  40.0, 14.0, 120, "1 slice"),
    "crepe":                      (180,  6.0,  24.0,  7.0,  80, "1 crepe"),
    "churros":                    (360,  5.0,  54.0, 14.0, 100, "1 serving"),
    "baklava":                    (450,  6.0,  52.0, 26.0, 100, "2 pieces"),

    # ── Fruits ───────────────────────────────────────────────────────────────
    "banana":                     ( 90,  1.1,  23.0,  0.3, 120, "1 medium"),
    "apple":                      ( 80,  0.4,  21.0,  0.2, 182, "1 medium"),
    "orange":                     ( 70,  1.3,  16.0,  0.2, 180, "1 medium"),
    "strawberry":                 ( 50,  1.0,  12.0,  0.5, 152, "1 cup"),
    "grape":                      ( 70,  0.7,  18.0,  0.2, 100, "1 cup"),
    "watermelon":                 ( 45,  0.9,  11.0,  0.2, 200, "1 slice"),
    "melon":                      ( 60,  0.8,  15.0,  0.2, 200, "1 slice"),
    "peach":                      ( 60,  1.4,  15.0,  0.4, 150, "1 medium"),
    "pear":                       (100,  0.6,  27.0,  0.2, 178, "1 medium"),
    "kiwi":                       ( 60,  1.1,  15.0,  0.5, 100, "1 medium"),
    "mango":                      (100,  1.4,  25.0,  0.6, 165, "1 cup"),
    "pineapple":                  ( 80,  0.9,  21.0,  0.2, 165, "1 cup"),
    "blueberry":                  ( 80,  1.0,  21.0,  0.5, 148, "1 cup"),
    "raspberry":                  ( 65,  1.5,  15.0,  0.8, 123, "1 cup"),
    "cherry":                     ( 50,  1.0,  12.0,  0.3, 100, "10 cherries"),
    "plum":                       ( 75,  1.1,  19.0,  0.4, 150, "2 medium"),
    "fig":                        ( 74,  0.8,  19.0,  0.3, 100, "2 medium"),
    "pomegranate":                ( 83,  1.7,  19.0,  1.2, 100, "1/2 fruit"),
    "lychee":                     ( 66,  0.8,  17.0,  0.4, 100, "5 lychees"),
    "papaya":                     ( 55,  0.6,  14.0,  0.4, 200, "1 cup"),

    # ── Vegetables ───────────────────────────────────────────────────────────
    "carrot":                     ( 52,  1.2,  12.0,  0.3, 100, "1 medium"),
    "broccoli":                   ( 55,  3.7,  11.0,  0.6, 100, "1 cup"),
    "corn":                       (130,  4.7,  29.0,  1.8, 154, "1 ear"),
    "asparagus":                  ( 40,  4.4,   7.0,  0.4, 100, "5 spears"),
    "avocado":                    (240,  3.0,  13.0, 22.0, 150, "1 medium"),
    "tomato":                     ( 35,  1.7,   7.0,  0.4, 180, "1 large"),
    "cucumber":                   ( 24,  1.1,   5.0,  0.2, 200, "1 cup"),
    "spinach":                    ( 41,  5.0,   6.8,  0.9, 100, "1 cup"),
    "mushroom":                   ( 35,  3.1,   5.0,  0.5, 100, "1 cup"),
    "eggplant":                   ( 35,  0.8,   9.0,  0.2, 100, "1 cup"),
    "sweet potato":               (180,  4.0,  41.0,  0.3, 200, "1 medium"),
    "potato":                     (130,  3.0,  30.0,  0.2, 180, "1 medium"),
    "pumpkin":                    ( 80,  2.0,  20.0,  0.2, 200, "1 cup"),
    "kabocha":                    ( 80,  2.0,  20.0,  0.2, 200, "1 cup"),
    "radish":                     ( 20,  0.7,   4.1,  0.1, 100, "5 slices"),
    "daikon":                     ( 18,  0.6,   4.1,  0.1, 100, "5 slices"),
    "burdock root":               ( 85,  1.8,  20.0,  0.1, 100, "100 g"),
    "gobo":                       ( 85,  1.8,  20.0,  0.1, 100, "100 g"),
}

# ---------------------------------------------------------------------------
# Aliases — map alternate / romanised / dataset variant names to _DB keys
# ---------------------------------------------------------------------------

_ALIASES: dict[str, str] = {
    # Japanese romanisation variants
    "unadon":               "eels on rice",
    "unaju":                "eels on rice",
    "oyako-don":            "chicken-n-egg on rice",
    "oyako don":            "chicken-n-egg on rice",
    "katsu-don":            "pork cutlet on rice",
    "katsu don":            "pork cutlet on rice",
    "ten-don":              "tendon",
    "gyuu-don":             "gyudon",
    "beef bowl":            "gyudon",
    "beef on rice":         "gyudon",
    "tekka-don":            "tekkadon",
    "tuna on rice":         "tekkadon",
    # Sushi variants
    "maki":                 "sushi",
    "maki sushi":           "sushi",
    "hand roll":            "temaki sushi",
    # Noodle variants
    "yakisoba noodles":     "yakisoba",
    "stir-fried noodles":   "yakisoba",
    "cold ramen":           "hiyashi chuka",
    "cold chinese noodles": "hiyashi chuka",
    "dipping noodles":      "tsukemen",
    "buckwheat noodles":    "soba",
    "cold soba":            "zaru soba",
    "wheat noodles":        "udon",
    # Curry variants
    "kare":                 "Japanese curry",
    "kare raisu":           "Japanese curry",
    "curry rice":           "Japanese curry",
    "katsu kare":           "Japanese curry",
    "gaeng keow wan":       "green curry",
    # Meat variants
    "karaage":              "chicken karaage",
    "kara-age":             "chicken karaage",
    "ebi furai":            "fried shrimp",
    "ebi fry":              "fried shrimp",
    "hambagu":              "hamburger steak",
    "hamburg steak":        "hamburger steak",
    "katsu":                "pork cutlet",
    "tori karaage":         "chicken karaage",
    "teriyaki":             "teriyaki chicken",
    # Japanese street food
    "tako-yaki":            "takoyaki",
    "okonomi-yaki":         "okonomiyaki",
    "japanese pancake":     "okonomiyaki",
    # Misc
    "rice ball":            "onigiri",
    "omusubi":              "onigiri",
    "tamagoyaki roll":      "tamagoyaki",
    "japanese omelette":    "tamagoyaki",
    "japanese omelet":      "tamagoyaki",
    "egg roll":             "egg rolls",
    "dumpling":             "dumplings",
    "pot sticker":          "gyoza",
    "potsticker":           "gyoza",
    "steamed bun":          "baozi",
    "bao":                  "baozi",
    "wonton":               "wontons",
    "french fry":           "french fries",
    "chips":                "potato chips",
    "fries":                "french fries",
    "naengmyeon":           "cold noodles",
    "bibim naengmyeon":     "cold noodles",
    "natto rice":           "natto",
    "fried tofu":           "agedashi tofu",
    "sweet potato tempura": "tempura",
    "eggplant nasu":        "eggplant",
    "satsumaimo":           "sweet potato",
    "saury":                "grilled saury",
    "sanma":                "grilled saury",
    "mackerel":             "grilled mackerel",
    "saba":                 "grilled mackerel",
    "eel":                  "eels on rice",
}

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    return name.strip().lower().replace("-", " ").replace("_", " ")


def _lookup(key: str) -> dict | None:
    """Return nutrient dict for normalised key, or None."""
    if key in _ALIASES:
        key = _ALIASES[key]
    entry = _DB.get(key)
    if entry is None:
        return None
    cal, pro, carb, fat, srv_g, srv_desc = entry
    return {
        "calories":    float(cal),
        "protein_g":   float(pro),
        "carbs_g":     float(carb),
        "fat_g":       float(fat),
        "serving_g":   srv_g,
        "serving_desc": srv_desc,
    }


def _partial_match(key: str) -> dict | None:
    """
    Try substring matching against DB keys and aliases.
    Returns the first entry whose key contains `key` as a substring,
    or whose `key` is a substring of the entry key.
    """
    # DB keys first
    for db_key in _DB:
        if key in db_key or db_key in key:
            return _lookup(db_key)
    # Then aliases
    for alias, target in _ALIASES.items():
        if key in alias or alias in key:
            return _lookup(target)
    return None


_ZERO: dict = {
    "calories": 0.0,
    "protein_g": 0.0,
    "carbs_g": 0.0,
    "fat_g": 0.0,
    "serving_g": 0,
    "serving_desc": "unknown",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_nutrition(food_name: str) -> dict:
    """
    Look up nutrition for *food_name*.

    Matching order
    --------------
    1. Exact normalised match in the database
    2. Exact normalised match in the alias table
    3. Partial / substring match
    4. Return zeroes and emit a warning

    Returns
    -------
    dict with keys: calories, protein_g, carbs_g, fat_g, serving_g, serving_desc
    """
    key = _normalise(food_name)

    result = _lookup(key)
    if result is not None:
        return result

    result = _partial_match(key)
    if result is not None:
        return result

    print(f"[nutrition] '{food_name}' not found in local database — returning zeros.")
    return dict(_ZERO)


def aggregate(food_list: list[str]) -> dict:
    """
    Sum nutrients for every food in *food_list*.

    Duplicate food names are counted once (de-duplication mirrors the
    live-detection behaviour where a single dish may be detected in
    multiple bounding boxes).

    Returns
    -------
    dict with keys: calories, protein_g, carbs_g, fat_g
        (serving_g / serving_desc are omitted from the aggregate)
    """
    totals: dict[str, float] = {"calories": 0.0, "protein_g": 0.0,
                                 "carbs_g": 0.0,  "fat_g": 0.0}
    seen: set[str] = set()
    for name in food_list:
        key = _normalise(name)
        if key in seen:
            continue
        seen.add(key)
        n = get_nutrition(name)
        for field in totals:
            totals[field] += n[field]
    return {k: round(v, 1) for k, v in totals.items()}
