# Dataset Phasing Plan

This document outlines the phased approach to building a comprehensive
South Asian food dataset of 200–300 high-value foods, organized by priority,
country coverage, and source.

---

## Phase 1: Base Ingredients from USDA (Target: ~80 foods)

**Source**: USDA FoodData Central (public domain / CC0)
**Verification status**: `pending_review`
**Timeline**: Immediate (no license hurdles)

These are raw/base ingredients that form the building blocks of South Asian
cuisine. USDA data is authoritative and freely available.

### 1.1 Grains & Cereals (~15)

| Food | Slug | Countries | Source ID |
|------|------|-----------|-----------|
| Basmati rice | `basmati-rice` | PK, IN, BD, LK, NP | FDC 169705 |
| Non-basmati white rice | `white-rice` | PK, IN, BD, LK, NP | FDC 169705 |
| Whole wheat flour (atta) | `whole-wheat-flour` | PK, IN, BD, NP | FDC 168916 |
| White rice flour | `rice-flour` | IN, BD, LK | FDC 168890 |
| Semolina (suji/rava) | `semolina` | PK, IN | FDC 168871 |
| Millet (bajra) | `bajra-millet` | IN, NP, PK | FDC 168889 |
| Sorghum (jowar) | `sorghum` | IN, NP | FDC 168893 |
| Finger millet (ragi) | `finger-millet` | IN, NP, LK | FDC 168888 |
| Oats | `oats` | PK, IN, BD | FDC 169745 |
| Corn/maize | `corn` | PK, IN, BD | FDC 170289 |
| Barley | `barley` | NP, IN, PK | FDC 168877 |
| Buckwheat | `buckwheat` | NP | FDC 168883 |
| Amaranth | `amaranth` | IN, NP | FDC 168881 |
| Foxtail millet | `foxtail-millet` | IN | FDC 168887 |
| Rice noodles | `rice-noodles` | BD, LK | FDC 168890 |

### 1.2 Legumes & Pulses (~12)

| Food | Slug | Countries |
|------|------|-----------|
| Red lentils (masoor dal) | `red-lentils` | PK, IN, BD, NP, LK |
| Yellow lentils (toor dal) | `yellow-lentils` | PK, IN |
| Black lentils (urad dal) | `black-lentils` | PK, IN |
| Chickpeas (chana) | `chickpeas` | PK, IN, BD, NP |
| Black-eyed peas (lobia) | `black-eyed-peas` | PK, IN, BD |
| Green gram (moong dal) | `green-mung-beans` | PK, IN, BD, NP |
| Kidney beans (rajma) | `kidney-beans` | PK, IN, NP |
| Black chickpeas (kala chana) | `black-chickpeas` | PK, IN, NP |
| Pigeon peas (arhar) | `pigeon-peas` | IN, BD |
| Fava beans (babri) | `fava-beans` | PK, NP |
| Green peas | `green-peas` | PK, IN, BD |
| Soybeans | `soybeans` | IN, BD |

### 1.3 Dairy (~8)

| Food | Slug | Countries |
|------|------|-----------|
| Plain yogurt (dahi) | `plain-yogurt` | PK, IN, BD, NP, LK |
| Milk (whole) | `whole-milk` | PK, IN, BD, NP, LK |
| Clarified butter (ghee) | `ghee` | PK, IN, BD, NP |
| Paneer | `paneer` | IN, NP |
| Butter (white) | `white-butter-makhan` | PK, IN, NP |
| Buttermilk (lassi) | `lassi` | PK, IN |
| Cream (malai) | `malai-cream` | PK, IN |
| Ricotta-style (chhena) | `chhena` | IN |

### 1.4 Oils & Fats (~6)

| Food | Slug | Countries |
|------|------|-----------|
| Mustard oil | `mustard-oil` | PK, IN, BD, NP |
| Sunflower oil | `sunflower-oil` | PK, IN, BD |
| Coconut oil | `coconut-oil` | IN, LK, BD |
| Vegetable oil (generic) | `vegetable-oil` | PK, IN, BD, LK, NP |
| Sesame oil (til ka tel) | `sesame-oil` | IN, PK |
| Olive oil | `olive-oil` | PK, IN |

### 1.5 Vegetables (~15)

| Food | Slug | Countries |
|------|------|-----------|
| Onion | `onion` | PK, IN, BD, LK, NP |
| Tomato | `tomato` | PK, IN, BD, LK, NP |
| Potato | `potato` | PK, IN, BD, NP |
| Eggplant (brinjal) | `eggplant` | PK, IN, BD, LK, NP |
| Okra (ladyfinger) | `okra` | PK, IN, BD |
| Bottle gourd (lauki) | `bottle-gourd` | PK, IN, NP |
| Bitter gourd (karela) | `bitter-gourd` | PK, IN, NP |
| Spinach (palak) | `spinach` | PK, IN, NP |
| Fenugreek leaves (methi) | `fenugreek-leaves` | PK, IN |
| Green chili | `green-chili` | PK, IN, BD, NP |
| Cauliflower | `cauliflower` | PK, IN, BD, NP |
| Cabbage | `cabbage` | PK, IN, BD, NP |
| Drumstick (moringa) | `drumstick-moringa` | IN, LK |
| Pointed gourd (parwal) | `pointed-gourd` | IN, NP |
| Radish (mooli) | `radish` | PK, IN, NP |

### 1.6 Fruits (~8)

| Food | Slug | Countries |
|------|------|-----------|
| Mango | `mango` | PK, IN, BD, LK, NP |
| Banana | `banana` | PK, IN, BD, LK, NP |
| Papaya | `papaya` | PK, IN, BD, LK |
| Guava | `guava` | PK, IN, BD, LK |
| Coconut (fresh) | `coconut` | IN, LK, BD |
| Lemon/lime | `lemon` | PK, IN, BD, NP |
| Pomegranate | `pomegranate` | PK, IN |
| Dates (khajoor) | `dates` | PK, IN, BD |

### 1.7 Proteins (~8)

| Food | Slug | Countries |
|------|------|-----------|
| Chicken (breast) | `chicken-breast` | PK, IN, BD, LK, NP |
| Chicken (leg/thigh) | `chicken-leg` | PK, IN, BD |
| Mutton/goat | `mutton` | PK, IN, BD, NP |
| Lamb | `lamb` | PK, IN |
| Egg (whole, boiled) | `boiled-egg` | PK, IN, BD, NP, LK |
| Beef | `beef` | PK, BD |
| Fish (rohu) | `rohu-fish` | IN, BD |
| Prawns/shrimp | `prawns` | PK, IN, BD, LK |

### 1.8 Spices & Condiments (~8)

| Food | Slug | Countries |
|------|------|-----------|
| Turmeric powder | `turmeric` | PK, IN, BD, NP, LK |
| Cumin seeds | `cumin-seeds` | PK, IN, BD, NP |
| Coriander powder | `coriander-powder` | PK, IN, BD, NP |
| Red chili powder | `red-chili-powder` | PK, IN, BD, NP |
| Garam masala | `garam-masala` | PK, IN, NP |
| Salt | `salt` | PK, IN, BD, LK, NP |
| Ginger | `ginger` | PK, IN, BD, NP |
| Garlic | `garlic` | PK, IN, BD, NP, LK |

---

## Phase 2: ICMR-NIN IFCT Foods (Target: ~60 foods)

**Source**: ICMR-NIN Indian Food Composition Tables 2017
**Verification status**: `pending_review`
**Timeline**: Pending license verification

These are Indian-specific foods not well covered by USDA.

### 2.1 Prepared Dishes (~25)

| Food | Slug | Notes |
|------|------|-------|
| Chicken biryani | `chicken-biryani` | Hyderabad/Punjabi variants |
| Vegetable biryani | `vegetable-biryani` | |
| Dal fry | `dal-fry` | |
| Dal makhani | `dal-makhani` | |
| Sambar | `sambar` | South Indian staple |
| Rasam | `rasam` | |
| Chole (chickpea curry) | `chole` | |
| Paneer butter masala | `paneer-butter-masala` | |
| Palak paneer | `palak-paneer` | |
| Aloo gobi | `aloo-gobi` | |
| Baingan bharta | `baingan-bharta` | |
| Rajma (kidney bean curry) | `rajma-curry` | |
| Chicken tikka masala | `chicken-tikka-masala` | |
| Butter chicken | `butter-chicken` | |
| Mutton rogan josh | `mutton-rogan-josh` | |
| Fish curry (south Indian) | `fish-curry-south` | |
| Egg curry | `egg-curry` | |
| Poha (flattened rice dish) | `poha` | |
| Upma | `upma` | |
| Idli | `idli` | |
| Dosa (plain) | `dosa-plain` | |
| Uttapam | `uttapam` | |
| Dhokla | `dhokla` | |
| Pav bhaji | `pav-bhaji` | |
| Aloo paratha | `aloo-paratha` | |

### 2.2 Snacks & Street Food (~15)

| Food | Slug | Notes |
|------|------|-------|
| Samosa | `samosa` | PK, IN |
| Pakora/bhajia | `pakora` | |
| Vada (medu vada) | `medu-vada` | |
| Bhel puri | `bhel-puri` | |
| Sev puri | `sev-puri` | |
| Dahi puri | `dahi-puri` | |
| Papadum | `papadum` | |
| Namak pare | `namak-pare` | |
| Mathri | `mathri` | |
| Chakli/murukku | `chakli` | |
| Banana chips | `banana-chips` | Kerala |
| Pani puri (golgappa) | `pani-puri` | |
| Aloo tikki | `aloo-tikki` | |
| Kachori | `kachori` | |
| Spring roll (Indian) | `indian-spring-roll` | |

### 2.3 Sweets & Desserts (~10)

| Food | Slug | Notes |
|------|------|-------|
| Gulab jamun | `gulab-jamun` | |
| Jalebi | `jalebi` | |
| Kheer (rice pudding) | `kheer` | |
| Gajar ka halwa | `gajar-halwa` | |
| Barfi (milk) | `barfi` | |
| Rasgulla | `rasgulla` | Bengali origin |
| Sandesh | `sandesh` | Bengali |
| Ladoo (besan) | `besan-ladoo` | |
| Rasmalai | `rasmalai` | |
| Shrikhand | `shrikhand` | |

### 2.4 Beverages (~5)

| Food | Slug | Notes |
|------|------|-------|
| Masala chai | `masala-chai` | |
| Lassi (sweet) | `sweet-lassi` | |
| Mango lassi | `mango-lassi` | |
| Jaljeera | `jaljeera` | |
| Nimbu pani (lemonade) | `nimbu-pani` | |

### 2.5 Staples & Breads (~5)

| Food | Slug | Notes |
|------|------|-------|
| Chapati/roti | `chapati` | |
| Naan | `naan` | |
| Paratha (plain) | `plain-paratha` | |
| Poori | `poori` | |
| Thepla | `thepla` | Gujarati |

---

## Phase 3: Pakistan-Specific Foods (Target: ~30 foods)

**Source**: PARC data + USDA cross-reference + community verification
**Verification status**: `unverified` (community) or `pending_review` (PARC)

### 3.1 Pakistani Dishes

| Food | Slug | Notes |
|------|------|-------|
| Nihari | `nihari` | Slow-cooked beef stew |
| Haleem | `haleem` | Lentil-meat porridge |
| Karahi (chicken) | `chicken-karahi` | |
| Karahi (mutton) | `mutton-karahi` | |
| Paye (trotters) | `paye` | |
| Siri paye | `siri-paye` | |
| Seekh kebab | `seekh-kebab` | |
| Chapli kebab | `chapli-kebab` | Peshawari |
| Biryani (Sindhi) | `sindhi-biryani` | |
| Pulao (yakhni) | `yakhni-pulao` | |
| Haleem | `haleem-pakistani` | |
| Saag (mustard greens) | `saag` | |
| Saag with makki roti | `saag-makki-roti` | |
| Aloo ka bharta | `aloo-bharta` | |
| Baingan ka bharta (Pakistani) | `pakistani-baingan-bharta` | |
| Daal chawal | `daal-chawal` | Simple lentils + rice |
| Fish fry (Lahore) | `lahori-fish-fry` | |
| Haleem | `haleem-multani` | |
| Siri paye | `siri-paye` | |
| Kunna (mutton) | `kunna` | Chinioti |
| Namkeen raan | `namkeen-raan` | |
| Warqi paratha | `warqi-paratha` | |
| Sheer khurma | `sheer-khurma` | |
| Rabri | `rabri` | |
| Falooda | `falooda` | |
| Kashmiri chai (noon chai) | `kashmiri-chai` | |
| Rooh afza drink | `rooh-afza` | |
| Sattu drink | `sattu-drink` | Bihar/UP |
| Lassi (Pakistani) | `pakistani-lassi` | |
| Dahi baray | `dahi-baray` | |

---

## Phase 4: Bangladesh-Specific Foods (Target: ~20 foods)

**Source**: IFST Bangladesh + community data

| Food | Slug | Notes |
|------|------|-------|
| Hilsa curry (ilish) | `ilish-curry` | National fish |
| Chingri malai curry | `chingri-malai-curry` | Prawn coconut curry |
| Panta bhat | `panta-bhat` | Fermented rice |
| Bhapa pitha | `bhapa-pitha` | Steamed rice cake |
| Chotpoti | `chotpoti` | Street food |
| Fuchka | `fuchka` | Bangladeshi pani puri |
| Jhal muri | `jhalmuri` | Puffed rice snack |
| Kacchi biryani | `kacchi-biryani` | Dhaka style |
| Tehari | `tehari` | Beef + rice |
| Morog polao | `morog-polao` | Chicken rice |
| Rezala | `rezala` | Mild meat curry |
| Shutki (dried fish) | `shutki` | Fermented dried fish |
| Begun bharta | `begun-bharta` | Eggplant mash |
| Alu bharta | `alu-bharta` | Mashed potato |
| Macher jhol | `macher-jhol` | Light fish curry |
| Pui shak | `pui-shak` | Malabar spinach |
| Doi bora | `doi-bora` | Yogurt dumplings |
| Malpua | `malpua` | Sweet pancake |
| Chomchom | `chomchom` | Sweet |

---

## Phase 5: Sri Lanka & Nepal Foods (Target: ~20 foods)

### Sri Lanka (~10)

| Food | Slug | Notes |
|------|------|-------|
| Rice and curry (generic) | `rice-and-curry-sl` | |
| Hoppers (appa) | `hoppers` | |
| String hoppers (idiyappa) | `string-hoppers` | |
| Pol sambol | `pol-sambol` | Coconut relish |
| Dhal curry (Sri Lankan) | `sl-dhal-curry` | |
| Kiribath (milk rice) | `kiribath` | |
| Wambatu moju | `wambatu-moju` | Eggplant pickle |
| Kottu roti | `kottu-roti` | |
| Lamprais | `lamprais` | Dutch-influenced |
| Wood apple juice | `wood-apple-juice` | |

### Nepal (~10)

| Food | Slug | Notes |
|------|------|-------|
| Dal bhat | `dal-bhat` | National dish |
| Momos (steamed) | `momos-steamed` | |
| Momos (fried) | `momos-fried` | |
| Sel roti | `sel-roti` | Ring-shaped rice bread |
| Gundruk | `gundruk` | Fermented leafy greens |
| Chatamari | `chatamari` | Nepali pizza |
| Bara (lentil pancake) | `bara` | |
| Yomari | `yomari` | Steamed dumpling |
| Newari khaja set | `newari-khaja` | |
| Thukpa | `thukpa` | Noodle soup |

---

## Phase 6: Community-Verified & Regional Variants (Target: ~10 foods)

**Source**: Internal estimates, community contributions
**Verification status**: `unverified`

These fill gaps where no authoritative source exists.

| Food | Slug | Notes |
|------|------|-------|
| Homemade garam masala | `homemade-garam-masala` | Recipe varies |
| Achar (mixed pickle) | `mixed-achar` | Regional variants |
| Papad (various) | `papad` | |
| Chutney (coriander-mint) | `coriander-mint-chutney` | |
| Tamarind chutney | `tamarind-chutney` | |
| Green chutney | `green-chutney` | |
| Raita (cucumber) | `cucumber-raita` | |
| Pickled mango (achar) | `mango-achar` | |
| Masala peanuts | `masala-peanuts` | |
| Sweet chutney (imli) | `sweet-imli-chutney` | |

---

## Country Coverage Summary

| Phase | PK | IN | BD | LK | NP | Total Foods |
|-------|----|----|----|----|----|----|
| 1 (USDA base) | ✓ | ✓ | ✓ | ✓ | ✓ | ~80 |
| 2 (ICMR-NIN) | ○ | ✓ | ○ | ○ | ○ | ~60 |
| 3 (Pakistan) | ✓ | ○ | ○ | ○ | ○ | ~30 |
| 4 (Bangladesh) | ○ | ○ | ✓ | ○ | ○ | ~20 |
| 5 (SL + Nepal) | ○ | ○ | ○ | ✓ | ✓ | ~20 |
| 6 (Community) | ✓ | ✓ | ✓ | ✓ | ✓ | ~10 |
| **Total** | | | | | | **~220** |

✓ = primary coverage  ○ = secondary/cross-reference coverage

---

## Source Assignment per Phase

| Phase | Primary Source | License | Raw Data OK? |
|-------|---------------|---------|--------------|
| 1 | USDA FoodData Central | Public domain (CC0) | Yes |
| 2 | ICMR-NIN IFCT 2017 | Pending verification | Pending |
| 3 | PARC + USDA cross-ref | Pending | Pending |
| 4 | IFST Bangladesh | Pending | Pending |
| 5 | SL/NP government tables | Pending | Pending |
| 6 | Internal / community | Internal | Yes |

---

## Quality Milestones

1. **Phase 1 complete**: 80 base ingredients with USDA provenance, all
   `pending_review`, Atwater cross-checks passing.
2. **Phase 2 complete**: 60 Indian foods with ICMR-NIN provenance
   (pending license).
3. **Cross-validation**: At least 20 foods appear in both USDA and ICMR-NIN
   for data quality comparison.
4. **All phases complete**: 200+ foods covering all 5 countries, each
   traceable to a documented source.
