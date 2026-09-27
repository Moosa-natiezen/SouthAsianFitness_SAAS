type FoodThumbnailVisual = {
  category: string;
  glyph: string;
  background: string;
  accent: string;
};

const categoryVisuals: Record<string, FoodThumbnailVisual> = {
  beverages: {
    category: "Beverages",
    glyph: "🥤",
    background: "linear-gradient(135deg, #DBEAFE, #EFF6FF 55%, #BAE6FD)",
    accent: "#2563EB",
  },
  breads: {
    category: "Breads",
    glyph: "🫓",
    background: "linear-gradient(135deg, #FDE68A, #FEF3C7 55%, #FDBA74)",
    accent: "#B45309",
  },
  dairy: {
    category: "Dairy",
    glyph: "🥛",
    background: "linear-gradient(135deg, #E0F2FE, #F0F9FF 55%, #DBEAFE)",
    accent: "#0284C7",
  },
  eggs: {
    category: "Eggs",
    glyph: "🥚",
    background: "linear-gradient(135deg, #FEF3C7, #FFFBEB 55%, #FDE68A)",
    accent: "#D97706",
  },
  fish: {
    category: "Fish",
    glyph: "🐟",
    background: "linear-gradient(135deg, #CFFAFE, #ECFEFF 55%, #A5F3FC)",
    accent: "#0891B2",
  },
  fruits: {
    category: "Fruits",
    glyph: "🍎",
    background: "linear-gradient(135deg, #FECACA, #FFF1F2 55%, #FED7AA)",
    accent: "#E11D48",
  },
  grains: {
    category: "Grains",
    glyph: "🌾",
    background: "linear-gradient(135deg, #FEF08A, #FEFCE8 55%, #FDE68A)",
    accent: "#A16207",
  },
  legumes: {
    category: "Legumes",
    glyph: "🫘",
    background: "linear-gradient(135deg, #FED7AA, #FFF7ED 55%, #FECACA)",
    accent: "#C2410C",
  },
  meats: {
    category: "Meats",
    glyph: "🍖",
    background: "linear-gradient(135deg, #FECACA, #FEF2F2 55%, #FDBA74)",
    accent: "#B91C1C",
  },
  "nuts-seeds": {
    category: "Nuts & seeds",
    glyph: "🥜",
    background: "linear-gradient(135deg, #E7D5B5, #FAF5EB 55%, #D6C2A1)",
    accent: "#854D0E",
  },
  "oils-fats": {
    category: "Oils & fats",
    glyph: "🫒",
    background: "linear-gradient(135deg, #D9F99D, #F7FEE7 55%, #BEF264)",
    accent: "#4D7C0F",
  },
  poultry: {
    category: "Poultry",
    glyph: "🍗",
    background: "linear-gradient(135deg, #FED7AA, #FFF7ED 55%, #FDBA74)",
    accent: "#C2410C",
  },
  "prepared-dishes": {
    category: "Prepared dishes",
    glyph: "🍛",
    background: "linear-gradient(135deg, #FDE68A, #FFF7ED 55%, #FDBA74)",
    accent: "#C2410C",
  },
  snacks: {
    category: "Snacks",
    glyph: "🥟",
    background: "linear-gradient(135deg, #FBCFE8, #FDF2F8 55%, #FED7AA)",
    accent: "#BE185D",
  },
  spices: {
    category: "Spices",
    glyph: "🌶️",
    background: "linear-gradient(135deg, #FECACA, #FFF1F2 55%, #FDBA74)",
    accent: "#DC2626",
  },
  sweeteners: {
    category: "Sweeteners",
    glyph: "🍯",
    background: "linear-gradient(135deg, #FDE68A, #FFFBEB 55%, #FCD34D)",
    accent: "#D97706",
  },
  vegetables: {
    category: "Vegetables",
    glyph: "🥬",
    background: "linear-gradient(135deg, #BBF7D0, #F0FDF4 55%, #D9F99D)",
    accent: "#15803D",
  },
};

const fallbackVisuals: FoodThumbnailVisual[] = [
  {
    category: "Food",
    glyph: "🍽️",
    background: "linear-gradient(135deg, #FDE68A, #FFF7ED 55%, #FED7AA)",
    accent: "#B45309",
  },
  {
    category: "Food",
    glyph: "🥘",
    background: "linear-gradient(135deg, #FBCFE8, #FFF1F2 55%, #FED7AA)",
    accent: "#BE185D",
  },
  {
    category: "Food",
    glyph: "🥗",
    background: "linear-gradient(135deg, #BBF7D0, #F0FDF4 55%, #FEF08A)",
    accent: "#15803D",
  },
  {
    category: "Food",
    glyph: "🍱",
    background: "linear-gradient(135deg, #BFDBFE, #EFF6FF 55%, #FBCFE8)",
    accent: "#2563EB",
  },
];

const categoryKeywords: Array<[string, RegExp]> = [
  ["prepared-dishes", /\b(curry|biryani|karahi|tikka|haleem|nihari|daal|dal|sabzi|korma|pulao)\b/],
  ["breads", /\b(roti|naan|paratha|chapati|bread|flatbread)\b/],
  ["grains", /\b(rice|grain|atta|flour|wheat|millet|oat|barley|quinoa)\b/],
  ["sweeteners", /\b(sweet|sugar|honey|jaggery|syrup|mithai|gulab|jamun|halwa)\b/],
  ["snacks", /\b(snack|samosa|pakora|chaat|namkeen)\b/],
  ["fish", /\b(fish|salmon|tuna|shrimp|prawn)\b/],
  ["poultry", /\b(chicken|turkey|poultry)\b/],
  ["meats", /\b(beef|mutton|lamb|goat|meat)\b/],
  ["legumes", /\b(lentil|bean|chickpea|chana|rajma|legume)\b/],
  ["nuts-seeds", /\b(nut|seed|almond|cashew|sesame|peanut)\b/],
  ["vegetables", /\b(vegetable|spinach|potato|tomato|okra|gourd|sabzi)\b/],
  ["fruits", /\b(fruit|mango|banana|apple|guava|papaya|date)\b/],
  ["dairy", /\b(dairy|milk|yogurt|curd|paneer|cheese|lassi)\b/],
  ["beverages", /\b(beverage|drink|tea|chai|coffee|juice|sherbet)\b/],
  ["spices", /\b(spice|masala|cumin|turmeric|chili|pepper)\b/],
  ["oils-fats", /\b(oil|ghee|fat)\b/],
  ["eggs", /\b(egg)\b/],
];

function normalize(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function getFoodThumbnailVisual(
  name: string,
  slug: string,
  categorySlug: string | null,
): FoodThumbnailVisual {
  const normalizedCategory = normalize(categorySlug ?? "");
  const categoryVisual = categoryVisuals[normalizedCategory];
  if (categoryVisual) return categoryVisual;

  const searchText = `${slug} ${name}`.toLowerCase();
  for (const [category, pattern] of categoryKeywords) {
    if (pattern.test(searchText)) return categoryVisuals[category];
  }

  const hash = Array.from(`${slug} ${name}`).reduce(
    (value, character) => (value * 31 + character.charCodeAt(0)) >>> 0,
    0,
  );
  const fallback = fallbackVisuals[hash % fallbackVisuals.length];
  const category =
    categorySlug?.trim().replace(/[-_]+/g, " ") || fallback.category;

  return { ...fallback, category };
}

export function FoodThumbnail({
  name,
  slug,
  categorySlug,
}: {
  name: string;
  slug: string;
  categorySlug: string | null;
}) {
  const visual = getFoodThumbnailVisual(name, slug, categorySlug);

  return (
    <div
      aria-label={`${name} ${visual.category.toLowerCase()} thumbnail`}
      className="relative flex h-full w-full items-center justify-center overflow-hidden"
      data-category={normalize(visual.category)}
      role="img"
      style={{ background: visual.background }}
    >
      <div
        aria-hidden="true"
        className="absolute -right-8 -top-10 h-32 w-32 rounded-full border"
        style={{ borderColor: `${visual.accent}20` }}
      />
      <div
        aria-hidden="true"
        className="absolute -bottom-14 -left-8 h-36 w-36 rounded-full border"
        style={{ borderColor: `${visual.accent}24` }}
      />
      <div
        aria-hidden="true"
        className="absolute h-20 w-20 rounded-full opacity-30 blur-2xl"
        style={{ backgroundColor: visual.accent }}
      />
      <span
        aria-hidden="true"
        className="relative z-10 select-none text-6xl drop-shadow-sm transition-transform duration-300 group-hover:scale-110"
      >
        {visual.glyph}
      </span>
      <span
        aria-hidden="true"
        className="absolute bottom-2 left-3 text-[9px] font-semibold uppercase tracking-[0.2em] opacity-70"
        style={{ color: visual.accent }}
      >
        {visual.category}
      </span>
    </div>
  );
}
