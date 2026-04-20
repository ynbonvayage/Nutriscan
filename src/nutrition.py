# Authors: Yu Cao, Na Yin, Fan Zhang
# Date: April 2026
# Purpose: Local nutrition database for all 194
#          NutriScan v2 food categories. Provides
#          get_nutrition() and aggregate() functions
#          for looking up calorie and macro data by
#          food label name. No external API required.
"""
Local nutrition database for all 194 NutriScan v2 classes.

Keys are the EXACT label strings output by the trained model —
underscores, hyphens, commas, ampersands, and capitalisation preserved.
They correspond line-for-line to classes_v2.txt.

No external API or network calls required.

Public API
----------
get_nutrition(food_name) -> dict
    Returns {calories, protein_g, carbs_g, fat_g, serving_g, serving_desc}.
    Primary path: exact key lookup.  Falls back to normalised/partial match,
    then zeroes on total miss.

aggregate(food_list) -> dict
    Sums nutrients across a list of food name strings (deduplicates by name).
"""

# ---------------------------------------------------------------------------
# Database — keys are exact model output labels (classes_v2.txt order)
# Each value: (calories, protein_g, carbs_g, fat_g, serving_g, serving_desc)
# Sources: USDA FoodData Central, Japanese Standard Tables of Food Composition
# (8th ed.), and standard culinary references.
# All numeric fields are non-zero (trace values set to 0.5 minimum).
# ---------------------------------------------------------------------------

_DB: dict[str, tuple] = {

    # ── Rice / grain bowls ─────────────────────────────────────────────────
    "eels_on_rice":                           (500, 27.0,  66.0, 14.0, 350, "1 bowl"),
    "pilaf":                                  (320, 10.0,  52.0,  8.0, 200, "1 serving"),
    "chicken-'n'-egg_on_rice":                (520, 28.0,  68.0, 12.0, 400, "1 bowl"),
    "pork_cutlet_on_rice":                    (680, 30.0,  78.0, 26.0, 450, "1 bowl"),
    "beef_curry":                             (500, 22.0,  58.0, 18.0, 400, "1 serving"),
    "sushi":                                  (350, 16.0,  56.0,  8.0, 200, "6 pieces"),
    "chicken_rice":                           (420, 20.0,  56.0, 10.0, 300, "1 plate"),
    "fried_rice":                             (400, 12.0,  58.0, 14.0, 250, "1 serving"),
    "tempura_bowl":                           (560, 20.0,  74.0, 18.0, 400, "1 bowl"),
    "bibimbap":                               (490, 20.0,  72.0, 12.0, 400, "1 bowl"),

    # ── Bread / baked ──────────────────────────────────────────────────────
    "toast":                                  (140,  4.5,  26.0,  2.5,  60, "2 slices"),
    "croissant":                              (230,  5.0,  26.0, 12.0,  57, "1 medium"),
    "roll_bread":                             (120,  3.5,  22.0,  2.0,  50, "1 roll"),
    "raisin_bread":                           (320,  8.0,  56.0,  7.0, 100, "2 slices"),

    # ── Burgers / fast food ────────────────────────────────────────────────
    "hamburger":                              (550, 28.0,  42.0, 28.0, 250, "1 burger"),
    "pizza":                                  (480, 20.0,  56.0, 18.0, 200, "2 slices"),
    "sandwiches":                             (380, 16.0,  46.0, 14.0, 200, "1 sandwich"),

    # ── Noodles ────────────────────────────────────────────────────────────
    "udon_noodle":                            (400, 13.0,  78.0,  2.0, 300, "1 bowl"),
    "tempura_udon":                           (550, 18.0,  82.0, 14.0, 400, "1 bowl"),
    "soba_noodle":                            (360, 14.0,  72.0,  2.0, 300, "1 bowl"),
    "ramen_noodle":                           (450, 22.0,  58.0, 14.0, 400, "1 bowl"),
    "beef_noodle":                            (480, 26.0,  56.0, 14.0, 350, "1 bowl"),
    "tensin_noodle":                          (420, 18.0,  60.0, 10.0, 350, "1 bowl"),
    "spaghetti":                              (380, 12.0,  66.0,  8.0, 250, "1 serving"),

    # ── Japanese pancake / battered ────────────────────────────────────────
    "Japanese-style_pancake":                 (320, 10.0,  48.0, 10.0, 200, "1 pancake"),
    "takoyaki":                               (260, 10.0,  32.0, 10.0, 150, "6 pieces"),

    # ── Cooked vegetables / side dishes ───────────────────────────────────
    "gratin":                                 (380, 16.0,  30.0, 22.0, 250, "1 serving"),
    "croquette":                              (280,  8.0,  30.0, 14.0, 100, "2 pieces"),
    "sauteed_spinach":                        ( 70,  4.0,   7.0,  3.5, 100, "1 serving"),
    "vegetable_tempura":                      (320,  4.0,  36.0, 16.0, 150, "1 serving"),

    # ── Soups ──────────────────────────────────────────────────────────────
    "potage":                                 (160,  4.0,  22.0,  6.0, 250, "1 bowl"),

    # ── Tempura / oden ─────────────────────────────────────────────────────
    "oden":                                   (200, 12.0,  24.0,  4.0, 400, "1 serving"),

    # ── Dumplings ──────────────────────────────────────────────────────────
    "jiaozi":                                 (260, 12.0,  30.0, 10.0, 180, "6 dumplings"),

    # ── Meat dishes ────────────────────────────────────────────────────────
    "stew":                                   (320, 20.0,  24.0, 14.0, 350, "1 bowl"),

    # ── Fish / seafood ─────────────────────────────────────────────────────
    "sashimi":                                (160, 26.0,   2.0,  5.0, 150, "6 pieces"),
    "grilled_pacific_saury":                  (220, 22.0,   0.5, 14.0, 120, "1 fish"),
    "sweet_and_sour_pork":                    (380, 20.0,  42.0, 14.0, 250, "1 serving"),
    "lightly_roasted_fish":                   (160, 22.0,   0.5,  8.0, 100, "1 serving"),

    # ── Egg dishes ─────────────────────────────────────────────────────────
    "steamed_egg_hotchpotch":                 (180, 12.0,   8.0, 10.0, 200, "1 serving"),

    # ── Meat dishes (continued) ────────────────────────────────────────────
    "seasoned_beef_with_potatoes":            (360, 18.0,  36.0, 14.0, 300, "1 serving"),
    "hambarg_steak":                          (380, 22.0,  14.0, 26.0, 180, "1 patty"),
    "steak":                                  (500, 40.0,   0.5, 36.0, 200, "1 serving"),
    "dried_fish":                             (180, 24.0,   0.5, 10.0,  80, "1 serving"),
    "ginger_pork_saute":                      (380, 26.0,  12.0, 24.0, 200, "1 serving"),

    # ── Tofu / soy ─────────────────────────────────────────────────────────
    "spicy_chili-flavored_tofu":              (240, 16.0,  10.0, 16.0, 200, "1 serving"),

    # ── Meat / skewers ─────────────────────────────────────────────────────
    "yakitori":                               (220, 18.0,   8.0, 12.0, 150, "5 skewers"),
    "cabbage_roll":                           (280, 16.0,  22.0, 12.0, 300, "2 rolls"),

    # ── Fermented / soy ────────────────────────────────────────────────────
    "natto":                                  (190, 16.0,  12.0, 10.0, 100, "1 pack"),

    # ── Egg dishes ─────────────────────────────────────────────────────────
    "egg_roll":                               (200,  8.0,  22.0,  8.0, 100, "2 pieces"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "chilled_noodle":                         (320, 12.0,  56.0,  5.0, 250, "1 serving"),

    # ── Meat dishes (continued) ────────────────────────────────────────────
    "stir-fried_beef_and_peppers":            (320, 24.0,  14.0, 18.0, 200, "1 serving"),
    "boiled_chicken_and_vegetables":          (260, 28.0,  14.0,  8.0, 350, "1 serving"),

    # ── Rice bowls (continued) ─────────────────────────────────────────────
    "sashimi_bowl":                           (480, 30.0,  60.0,  8.0, 350, "1 bowl"),

    # ── Japanese pancake / battered ────────────────────────────────────────
    "fish-shaped_pancake_with_bean_jam":      (180,  4.0,  36.0,  3.0, 100, "2 pieces"),

    # ── Chicken ────────────────────────────────────────────────────────────
    "roast_chicken":                          (350, 36.0,   0.5, 22.0, 200, "1 serving"),

    # ── Dumplings (continued) ──────────────────────────────────────────────
    "steamed_meat_dumpling":                  (180, 10.0,  22.0,  6.0, 120, "3 pieces"),

    # ── Rice bowls (continued) ─────────────────────────────────────────────
    "omelet_with_fried_rice":                 (520, 16.0,  68.0, 20.0, 350, "1 serving"),
    "cutlet_curry":                           (680, 30.0,  78.0, 26.0, 450, "1 plate"),

    # ── Pasta ──────────────────────────────────────────────────────────────
    "spaghetti_meat_sauce":                   (480, 22.0,  62.0, 16.0, 300, "1 serving"),

    # ── Seafood ────────────────────────────────────────────────────────────
    "fried_shrimp":                           (300, 20.0,  22.0, 14.0, 150, "5 pieces"),

    # ── Salads ─────────────────────────────────────────────────────────────
    "potato_salad":                           (200,  4.0,  24.0, 10.0, 150, "1 serving"),
    "macaroni_salad":                         (280,  6.0,  30.0, 16.0, 150, "1 serving"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "Japanese_tofu_and_vegetable_chowder":    (160,  8.0,  18.0,  6.0, 300, "1 bowl"),
    "chinese_soup":                           ( 80,  5.0,   8.0,  3.0, 250, "1 bowl"),

    # ── Rice bowls (continued) ─────────────────────────────────────────────
    "beef_bowl":                              (560, 22.0,  72.0, 18.0, 400, "1 bowl"),

    # ── Vegetable dishes ───────────────────────────────────────────────────
    "kinpira-style_sauteed_burdock":          (120,  3.0,  18.0,  4.0, 100, "1 serving"),

    # ── Bread / baked (continued) ──────────────────────────────────────────
    "pizza_toast":                            (280, 10.0,  36.0, 10.0, 120, "1 slice"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "dipping_noodles":                        (420, 18.0,  68.0,  6.0, 350, "1 serving"),

    # ── Fast food ──────────────────────────────────────────────────────────
    "hot_dog":                                (280, 11.0,  24.0, 16.0, 120, "1 hot dog"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "mixed_rice":                             (380, 12.0,  62.0,  8.0, 250, "1 serving"),

    # ── Vegetable dishes (continued) ──────────────────────────────────────
    "goya_chanpuru":                          (280, 18.0,  12.0, 16.0, 250, "1 serving"),

    # ── Curries ────────────────────────────────────────────────────────────
    "green_curry":                            (380, 22.0,  24.0, 22.0, 300, "1 serving"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "okinawa_soba":                           (380, 16.0,  54.0, 10.0, 350, "1 bowl"),

    # ── Desserts ───────────────────────────────────────────────────────────
    "mango_pudding":                          (160,  3.0,  28.0,  5.0, 150, "1 serving"),
    "almond_jelly":                           (120,  2.0,  22.0,  3.0, 150, "1 serving"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "jjigae":                                 (280, 18.0,  16.0, 14.0, 350, "1 serving"),

    # ── Meat (continued) ───────────────────────────────────────────────────
    "dak_galbi":                              (380, 30.0,  24.0, 18.0, 250, "1 serving"),

    # ── Rice / curries ─────────────────────────────────────────────────────
    "dry_curry":                              (420, 16.0,  56.0, 14.0, 300, "1 serving"),
    "kamameshi":                              (420, 16.0,  68.0,  8.0, 300, "1 serving"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "rice_vermicelli":                        (280,  6.0,  62.0,  1.0, 200, "1 serving"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "paella":                                 (500, 22.0,  60.0, 16.0, 350, "1 serving"),

    # ── Tempura / fried ────────────────────────────────────────────────────
    "kushikatu":                              (420, 18.0,  32.0, 24.0, 150, "5 skewers"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "pancake":                                (260,  6.0,  36.0, 10.0, 150, "2 pancakes"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "champon":                                (520, 26.0,  66.0, 14.0, 450, "1 bowl"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "crape":                                  (240,  6.0,  34.0,  9.0, 150, "1 crepe"),
    "tiramisu":                               (420,  8.0,  40.0, 26.0, 150, "1 serving"),
    "rare_cheese_cake":                       (380,  6.0,  32.0, 26.0, 120, "1 slice"),
    "shortcake":                              (320,  5.0,  42.0, 14.0, 100, "1 slice"),

    # ── Chinese / stir-fry ─────────────────────────────────────────────────
    "chop_suey":                              (280, 18.0,  22.0, 12.0, 300, "1 serving"),
    "twice_cooked_pork":                      (380, 20.0,  14.0, 28.0, 200, "1 serving"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "mushroom_risotto":                       (360, 10.0,  58.0, 10.0, 300, "1 serving"),

    # ── Korean ─────────────────────────────────────────────────────────────
    "samul":                                  (320, 18.0,  22.0, 16.0, 250, "1 serving"),

    # ── Japanese soups / rice cakes ────────────────────────────────────────
    "zoni":                                   (220,  8.0,  32.0,  5.0, 300, "1 bowl"),

    # ── Egg dishes (continued) ─────────────────────────────────────────────
    "french_toast":                           (290,  9.0,  36.0, 12.0, 150, "2 slices"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "fine_white_noodles":                     (280,  9.0,  58.0,  1.0, 200, "1 serving"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "minestrone":                             (160,  6.0,  26.0,  4.0, 300, "1 bowl"),

    # ── French / European ──────────────────────────────────────────────────
    "pot_au_feu":                             (300, 22.0,  24.0, 12.0, 350, "1 serving"),

    # ── Fast food (continued) ──────────────────────────────────────────────
    "chicken_nugget":                         (280, 16.0,  18.0, 16.0, 100, "5 pieces"),

    # ── Fish / seafood (continued) ─────────────────────────────────────────
    "namero":                                 (180, 18.0,   6.0,  8.0, 100, "1 serving"),

    # ── Bread (continued) ──────────────────────────────────────────────────
    "french_bread":                           (280,  9.0,  54.0,  2.0, 100, "2 slices"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "rice_gruel":                             (120,  3.0,  26.0,  0.5, 300, "1 bowl"),
    "broiled_eel_bowl":                       (480, 28.0,  60.0, 14.0, 350, "1 bowl"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "clear_soup":                             ( 30,  2.0,   3.0,  0.5, 200, "1 bowl"),

    # ── Tofu (continued) ───────────────────────────────────────────────────
    "yudofu":                                 (100, 10.0,   4.0,  5.0, 300, "1 serving"),

    # ── Seaweed ────────────────────────────────────────────────────────────
    "mozuku":                                 ( 15,  0.4,   3.0,  0.1, 100, "1 serving"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "inarizushi":                             (320,  8.0,  58.0,  7.0, 180, "3 pieces"),

    # ── Meat (continued) ───────────────────────────────────────────────────
    "thinly_sliced_raw_horsemeat":            (110, 20.0,   1.0,  2.5, 100, "100 g"),

    # ── Bread (continued) ──────────────────────────────────────────────────
    "bagel":                                  (270, 10.0,  52.0,  1.5, 105, "1 medium"),
    "scone":                                  (200,  4.0,  28.0,  8.0,  60, "1 scone"),
    "tortilla":                               (150,  4.0,  28.0,  3.0,  50, "1 small"),

    # ── Mexican / Tex-Mex ──────────────────────────────────────────────────
    "tacos":                                  (380, 18.0,  34.0, 18.0, 200, "2 tacos"),
    "nachos":                                 (440, 12.0,  52.0, 22.0, 200, "1 serving"),

    # ── Egg dishes (continued) ─────────────────────────────────────────────
    "scrambled_egg":                          (200, 14.0,   2.0, 14.0, 150, "2 eggs"),

    # ── Rice / baked ───────────────────────────────────────────────────────
    "rice_gratin":                            (420, 16.0,  48.0, 18.0, 300, "1 serving"),

    # ── Pasta / baked ──────────────────────────────────────────────────────
    "lasagna":                                (480, 22.0,  44.0, 22.0, 300, "1 serving"),

    # ── Salads (continued) ─────────────────────────────────────────────────
    "Caesar_salad":                           (360,  8.0,  16.0, 30.0, 200, "1 serving"),

    # ── Cereals ────────────────────────────────────────────────────────────
    "oatmeal":                                (160,  6.0,  28.0,  3.0, 240, "1 serving"),

    # ── Dumplings (continued) ──────────────────────────────────────────────
    "fried_pork_dumplings_served_in_soup":    (380, 16.0,  46.0, 14.0, 350, "1 serving"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "oshiruko":                               (240,  5.0,  50.0,  2.0, 200, "1 bowl"),
    "muffin":                                 (380,  6.0,  56.0, 14.0, 100, "1 muffin"),
    "popcorn":                                (380,  6.0,  70.0, 10.0, 100, "1 serving"),
    "cream_puff":                             (280,  5.0,  30.0, 16.0,  80, "1 puff"),
    "doughnut":                               (300,  4.0,  38.0, 14.0,  70, "1 doughnut"),
    "apple_pie":                              (320,  3.0,  46.0, 14.0, 125, "1 slice"),
    "parfait":                                (380,  6.0,  56.0, 16.0, 300, "1 serving"),

    # ── Pork dishes ────────────────────────────────────────────────────────
    "fried_pork_in_scoop":                    (480, 22.0,  52.0, 18.0, 250, "1 serving"),
    "lamb_kebabs":                            (300, 24.0,   6.0, 20.0, 120, "3 skewers"),

    # ── Vegetable dishes (continued) ──────────────────────────────────────
    # NOTE: exact label has comma after "potato" — preserved as-is
    "dish_consisting_of_stir-fried_potato,_eggplant_and_green_pepper":
                                              (200,  5.0,  28.0,  8.0, 200, "1 serving"),

    # ── Hot pot ────────────────────────────────────────────────────────────
    "hot_pot":                                (400, 28.0,  20.0, 22.0, 400, "1 serving"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "moon_cake":                              (380,  6.0,  58.0, 14.0, 100, "1 piece"),
    "custard_tart":                           (280,  6.0,  34.0, 14.0, 100, "1 tart"),

    # ── Noodle soups (continued) ───────────────────────────────────────────
    "beef_noodle_soup":                       (580, 30.0,  68.0, 18.0, 450, "1 bowl"),

    # ── Meat (continued) ───────────────────────────────────────────────────
    "pork_cutlet":                            (440, 28.0,  24.0, 26.0, 200, "1 cutlet"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "fish_ball_soup":                         (140, 12.0,  10.0,  4.0, 250, "1 bowl"),

    # ── Egg dishes (continued) ─────────────────────────────────────────────
    "oyster_omelette":                        (300, 14.0,  28.0, 14.0, 200, "1 serving"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "glutinous_oil_rice":                     (400, 10.0,  72.0,  8.0, 250, "1 serving"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "trunip_pudding":                         (180,  4.0,  34.0,  4.0, 150, "1 serving"),

    # ── Tofu (continued) ───────────────────────────────────────────────────
    "stinky_tofu":                            (200, 12.0,  10.0, 12.0, 150, "1 serving"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "lemon_fig_jelly":                        (100,  1.0,  24.0,  0.5, 150, "1 serving"),

    # ── Curries (continued) ────────────────────────────────────────────────
    "khao_soi":                               (580, 24.0,  60.0, 26.0, 400, "1 bowl"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "Sour_prawn_soup":                        (180, 16.0,   8.0,  8.0, 300, "1 bowl"),

    # ── Salads (continued) ─────────────────────────────────────────────────
    "Thai_papaya_salad":                      (130,  4.0,  20.0,  4.0, 200, "1 serving"),

    # ── Southeast Asian (continued) ────────────────────────────────────────
    # NOTE: exact label has comma after "boned" — preserved as-is
    "boned,_sliced_Hainan-style_chicken_with_marinated_rice":
                                              (520, 30.0,  56.0, 16.0, 400, "1 plate"),
    # NOTE: exact label has comma after "sour" — preserved as-is
    "hot_and_sour,_fish_and_vegetable_ragout":
                                              (240, 20.0,  18.0,  9.0, 350, "1 serving"),

    # ── Vegetable dishes (continued) ──────────────────────────────────────
    "stir-fried_mixed_vegetables":            (120,  4.0,  14.0,  5.0, 200, "1 serving"),

    # ── Meat (continued) ───────────────────────────────────────────────────
    "pork_satay":                             (360, 24.0,  14.0, 22.0, 150, "5 skewers"),
    "spicy_chicken_salad":                    (280, 24.0,  14.0, 14.0, 200, "1 serving"),

    # ── Noodles (continued) ────────────────────────────────────────────────
    "Pork_Sticky_Noodles":                    (480, 22.0,  62.0, 16.0, 380, "1 serving"),

    # ── Meat (continued) ───────────────────────────────────────────────────
    "charcoal-boiled_pork_neck":              (400, 28.0,   4.0, 30.0, 200, "1 serving"),
    "fried_mussel_pancakes":                  (340, 16.0,  32.0, 16.0, 200, "1 serving"),
    "Deep_Fried_Chicken_Wing":                (380, 24.0,  16.0, 24.0, 150, "3 wings"),

    # ── Rice plates (continued) ────────────────────────────────────────────
    "Barbecued_red_pork_in_sauce_with_rice":  (540, 24.0,  64.0, 18.0, 350, "1 plate"),
    "Rice_with_roast_duck":                   (520, 28.0,  56.0, 18.0, 350, "1 plate"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "Wonton_soup":                            (280, 14.0,  32.0, 10.0, 350, "1 bowl"),

    # ── Noodle soups (continued) ───────────────────────────────────────────
    "Hue_beef_rice_vermicelli_soup":          (480, 24.0,  58.0, 14.0, 450, "1 bowl"),
    "Vermicelli_noodles_with_snails":         (380, 18.0,  58.0,  8.0, 400, "1 bowl"),

    # ── Southeast Asian (continued) ────────────────────────────────────────
    "Steamed_rice_roll":                      (240,  8.0,  44.0,  4.0, 200, "1 serving"),

    # ── Seafood (continued) ────────────────────────────────────────────────
    "Shrimp_patties":                         (240, 16.0,  16.0, 12.0, 120, "4 pieces"),

    # ── Southeast Asian (continued) ────────────────────────────────────────
    "Coconut_milk-flavored_crepes_with_shrimp_and_beef":
                                              (320, 16.0,  36.0, 12.0, 200, "1 serving"),
    "Small_steamed_savory_rice_pancake":      (200,  6.0,  36.0,  4.0, 150, "1 serving"),

    # ── Dumplings (continued) ──────────────────────────────────────────────
    "Glutinous_Rice_Balls":                   (240,  4.0,  48.0,  4.0, 150, "4 balls"),

    # ── Hawaiian ───────────────────────────────────────────────────────────
    "loco_moco":                              (680, 34.0,  68.0, 28.0, 450, "1 serving"),
    "haupia":                                 (180,  1.0,  24.0, 10.0, 100, "1 serving"),
    "malasada":                               (280,  5.0,  36.0, 14.0,  80, "1 piece"),
    "spam_musubi":                            (280, 10.0,  38.0,  8.0, 150, "1 piece"),

    # ── Filipino ───────────────────────────────────────────────────────────
    "adobo":                                  (420, 30.0,  12.0, 28.0, 250, "1 serving"),
    "lumpia":                                 (220,  8.0,  22.0, 12.0, 100, "2 rolls"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "brownie":                                (340,  4.0,  46.0, 16.0,  80, "1 brownie"),
    "churro":                                 (260,  4.0,  36.0, 12.0,  80, "1 churro"),

    # ── Cajun / Southern ───────────────────────────────────────────────────
    "jambalaya":                              (420, 22.0,  48.0, 14.0, 300, "1 serving"),

    # ── Indonesian ─────────────────────────────────────────────────────────
    "nasi_goreng":                            (480, 16.0,  66.0, 16.0, 300, "1 serving"),
    "ayam_bakar":                             (320, 32.0,   6.0, 18.0, 200, "1 serving"),
    "bubur_ayam":                             (280, 14.0,  40.0,  6.0, 350, "1 bowl"),
    "mie_goreng":                             (440, 16.0,  58.0, 16.0, 300, "1 serving"),
    "nasi_padang":                            (620, 26.0,  80.0, 22.0, 400, "1 plate"),
    "nasi_uduk":                              (480, 12.0,  74.0, 16.0, 300, "1 serving"),
    "babi_guling":                            (480, 30.0,  10.0, 38.0, 200, "1 serving"),

    # ── Singapore / Malaysian ──────────────────────────────────────────────
    "kaya_toast":                             (320,  7.0,  44.0, 14.0, 120, "1 serving"),
    "bak_kut_teh":                            (280, 24.0,   6.0, 18.0, 350, "1 bowl"),
    "curry_puff":                             (320,  8.0,  38.0, 16.0, 120, "2 pieces"),

    # ── Chinese (continued) ────────────────────────────────────────────────
    "zha_jiang_mian":                         (520, 22.0,  68.0, 18.0, 350, "1 bowl"),
    "kung_pao_chicken":                       (360, 28.0,  16.0, 20.0, 200, "1 serving"),
    "crullers":                               (340,  8.0,  44.0, 16.0, 100, "2 pieces"),
    "eggplant_with_garlic_sauce":             (160,  4.0,  18.0,  8.0, 200, "1 serving"),
    "three_cup_chicken":                      (400, 30.0,  14.0, 24.0, 250, "1 serving"),
    "bean_curd_family_style":                 (200, 14.0,  10.0, 12.0, 200, "1 serving"),

    # NOTE: exact label uses & instead of "and" — preserved as-is
    "salt_&_pepper_fried_shrimp_with_shell":  (240, 22.0,   8.0, 14.0, 150, "1 serving"),

    # ── Fish (continued) ───────────────────────────────────────────────────
    "baked_salmon":                           (280, 30.0,   0.5, 16.0, 150, "1 fillet"),

    # ── Pork (continued) ───────────────────────────────────────────────────
    "braised_pork_meat_ball_with_napa_cabbage": (380, 22.0, 14.0, 26.0, 300, "1 serving"),

    # ── Soups (continued) ──────────────────────────────────────────────────
    "winter_melon_soup":                      ( 80,  4.0,  12.0,  2.0, 300, "1 bowl"),

    # ── Pork (continued) ───────────────────────────────────────────────────
    "steamed_spareribs":                      (320, 22.0,   8.0, 22.0, 150, "1 serving"),

    # ── Desserts (continued) ───────────────────────────────────────────────
    "chinese_pumpkin_pie":                    (280,  6.0,  42.0, 10.0, 150, "1 serving"),

    # ── Rice (continued) ───────────────────────────────────────────────────
    "eight_treasure_rice":                    (380,  6.0,  72.0,  8.0, 200, "1 serving"),

    # NOTE: exact label uses & instead of "and" — preserved as-is
    "hot_&_sour_soup":                        (120,  8.0,  12.0,  4.0, 250, "1 bowl"),
}

# ---------------------------------------------------------------------------
# Zero fallback
# ---------------------------------------------------------------------------

_ZERO: dict = {
    "calories":     0.0,
    "protein_g":    0.0,
    "carbs_g":      0.0,
    "fat_g":        0.0,
    "serving_g":    0,
    "serving_desc": "unknown",
}


def _row_to_dict(v: tuple) -> dict:
    """
    Convert a _DB tuple to a nutrition dict with named fields.
    v: (calories, protein_g, carbs_g, fat_g, serving_g, serving_desc).
    Returns dict with float/int typed values.
    """
    return {
        "calories":     float(v[0]),
        "protein_g":    float(v[1]),
        "carbs_g":      float(v[2]),
        "fat_g":        float(v[3]),
        "serving_g":    int(v[4]),
        "serving_desc": v[5],
    }


def get_nutrition(food_name: str) -> dict:
    """
    Look up nutrition data for food_name and return a dict of macro values.
    Tries exact match, then normalised match, then substring match, then zeros.
    food_name: label string as output by the model.
    """
    # 1. Exact match — primary path (covers all 194 model labels directly)
    if food_name in _DB:
        return _row_to_dict(_DB[food_name])

    # 2. Normalised match — handles minor variations in punctuation or case
    def _norm(s: str) -> str:
        return (
            s.lower()
             .replace("_", " ")
             .replace("-", " ")
             .replace(",", "")
             .replace("&", "and")
             .replace("'", "")
             .strip()
        )

    key_norm = _norm(food_name)
    for db_key, v in _DB.items():
        if _norm(db_key) == key_norm:
            return _row_to_dict(v)

    # 3. Partial / substring match — best-effort for unseen label variants
    for db_key, v in _DB.items():
        db_norm = _norm(db_key)
        if key_norm in db_norm or db_norm in key_norm:
            return _row_to_dict(v)

    print(f"[nutrition] '{food_name}' not found in local database — returning zeros.")
    return dict(_ZERO)


def aggregate(food_list: list) -> dict:
    """
    Sum nutrition totals across a list of food names, deduplicating by name.
    food_list: list of label strings (duplicates counted only once).
    Returns dict with rounded totals for calories, protein_g, carbs_g, fat_g.
    """
    totals: dict = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    seen: set = set()

    # Skip already-seen names to avoid double-counting the same food
    for name in food_list:
        key = name.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        n = get_nutrition(name)
        for field in totals:
            totals[field] += n[field]

    return {k: round(v, 1) for k, v in totals.items()}
