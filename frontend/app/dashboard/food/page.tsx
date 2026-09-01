"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getFoodCategories,
  searchFoods,
  type FoodCategory,
  type FoodItem,
} from "@/lib/api";

/* ── Constants ─────────────────────────────────────────────────────────── */

const PAGE_SIZE = 20;

const inputClass =
  "w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 transition-all focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/30";

/* ── Helpers ───────────────────────────────────────────────────────────── */

function formatMacro(value: number): string {
  return value % 1 === 0 ? String(value) : value.toFixed(1);
}

function formatServing(size: number, unit: string): string {
  return `${formatMacro(size)} ${unit}`;
}

/* ── FoodCard component ────────────────────────────────────────────────── */

function FoodCard({ food }: { food: FoodItem }) {
  return (
    <Card className="flex flex-col gap-3 py-4">
      <CardContent className="space-y-3">
        {/* Header: name + category */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold leading-snug text-white">
            {food.name}
          </h3>
          {food.category && (
            <Badge variant="secondary" className="shrink-0 text-xs">
              {food.category}
            </Badge>
          )}
        </div>

        {/* Description */}
        {food.description && (
          <p className="text-xs leading-relaxed text-zinc-400 line-clamp-2">
            {food.description}
          </p>
        )}

        {/* Serving */}
        <p className="text-xs text-zinc-500">
          Per {formatServing(food.serving_size, food.serving_unit)}
        </p>

        {/* Nutrition macros */}
        <div className="grid grid-cols-4 gap-2">
          <NutrientPill label="Cal" value={formatMacro(food.nutrition.calories)} unit="kcal" />
          <NutrientPill label="Protein" value={formatMacro(food.nutrition.protein_g)} unit="g" />
          <NutrientPill label="Carbs" value={formatMacro(food.nutrition.carbs_g)} unit="g" />
          <NutrientPill label="Fat" value={formatMacro(food.nutrition.fat_g)} unit="g" />
        </div>

        {/* Micro-nutrition */}
        {(food.nutrition.sugar_g != null || food.nutrition.sodium_mg != null) && (
          <div className="flex gap-3 text-xs text-zinc-500">
            {food.nutrition.sugar_g != null && (
              <span>Sugar {formatMacro(food.nutrition.sugar_g)}g</span>
            )}
            {food.nutrition.sodium_mg != null && (
              <span>Sodium {formatMacro(food.nutrition.sodium_mg)}mg</span>
            )}
          </div>
        )}

        {/* Tags */}
        {(food.dietary_tags.length > 0 || food.cuisine_tags.length > 0) && (
          <div className="flex flex-wrap gap-1">
            {food.dietary_tags.map((t) => (
              <Badge key={`d-${t}`} variant="outline" className="text-[10px]">
                {t}
              </Badge>
            ))}
            {food.cuisine_tags.map((t) => (
              <Badge key={`c-${t}`} variant="outline" className="text-[10px]">
                {t}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ── NutrientPill ──────────────────────────────────────────────────────── */

function NutrientPill({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit: string;
}) {
  return (
    <div className="rounded-md bg-white/[0.04] px-2 py-1 text-center">
      <p className="text-[10px] font-medium uppercase text-zinc-500">{label}</p>
      <p className="text-sm font-semibold text-zinc-200">
        {value}
        <span className="text-[10px] font-normal text-zinc-500"> {unit}</span>
      </p>
    </div>
  );
}

/* ── Skeleton grid ─────────────────────────────────────────────────────── */

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-48 rounded-xl" />
      ))}
    </div>
  );
}

/* ── Page component ────────────────────────────────────────────────────── */

export default function FoodLibraryPage() {
  /* ── State ────────────────────────────────────────────────────────── */
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState<FoodCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const offsetRef = useRef(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* ── Fetch foods ──────────────────────────────────────────────────── */

  const fetchFoods = useCallback(
    async (
      query: string,
      categorySlug: string | null,
      reset: boolean = false,
    ) => {
      if (reset) {
        offsetRef.current = 0;
        setFoods([]);
      }

      const offset = reset ? 0 : offsetRef.current;

      try {
        const result = await searchFoods({
          q: query || undefined,
          category_slug: categorySlug || undefined,
          limit: PAGE_SIZE,
          offset,
          verification_status: undefined,
        });

        if (reset) {
          setFoods(result.items);
        } else {
          setFoods((prev) => [...prev, ...result.items]);
        }
        setTotal(result.total);
        offsetRef.current = offset + result.items.length;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load foods.",
        );
      }
    },
    [],
  );

  /* ── Initial load ─────────────────────────────────────────────────── */

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [cats] = await Promise.all([
          getFoodCategories(),
          fetchFoods("", null, true),
        ]);
        if (!cancelled) setCategories(cats);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [fetchFoods]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Search with debounce ─────────────────────────────────────────── */

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setError(null);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void fetchFoods(value, selectedCategory, true);
    }, 300);
  };

  /* ── Category filter ──────────────────────────────────────────────── */

  const handleCategoryClick = (slug: string | null) => {
    const newCategory = slug === selectedCategory ? null : slug;
    setSelectedCategory(newCategory);
    setError(null);
    void fetchFoods(searchQuery, newCategory, true);
  };

  /* ── Load more ────────────────────────────────────────────────────── */

  const handleLoadMore = async () => {
    setLoadingMore(true);
    try {
      await fetchFoods(searchQuery, selectedCategory, false);
    } finally {
      setLoadingMore(false);
    }
  };

  const hasMore = foods.length < total;

  /* ── Render ──────────────────────────────────────────────────────── */

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Food Library</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Browse {total} verified South Asian foods with full nutrition data.
        </p>
      </div>

      {/* Error */}
      {error && <AlertBanner variant="error" message={error} />}

      {/* Search bar */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search foods by name..."
          className={inputClass}
          aria-label="Search foods"
        />
        <svg
          className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-zinc-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {/* Category filter pills */}
      {categories.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1" role="tablist">
          <button
            onClick={() => handleCategoryClick(null)}
            className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
              selectedCategory === null
                ? "border-emerald-600 bg-emerald-600 text-white"
                : "border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:bg-white/[0.06]"
            }`}
            role="tab"
            aria-selected={selectedCategory === null}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.slug}
              onClick={() => handleCategoryClick(cat.slug)}
              className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                selectedCategory === cat.slug
                  ? "border-emerald-600 bg-emerald-600 text-white"
                  : "border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:bg-white/[0.06]"
              }`}
              role="tab"
              aria-selected={selectedCategory === cat.slug}
            >
              {cat.name}
            </button>
          ))}
        </div>
      )}

      {/* Loading state */}
      {loading && <SkeletonGrid />}

      {/* Food grid */}
      {!loading && foods.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {foods.map((food) => (
            <FoodCard key={food.id} food={food} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && foods.length === 0 && (
        <div className="rounded-xl border border-dashed border-white/[0.08] bg-white/[0.01] py-16 text-center">
          <p className="text-sm font-medium text-zinc-400">
            No foods found matching your criteria.
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Try a different search term or category.
          </p>
        </div>
      )}

      {/* Load more */}
      {!loading && hasMore && (
        <div className="flex justify-center pt-2">
          <Button
            variant="outline"
            onClick={handleLoadMore}
            disabled={loadingMore}
          >
            {loadingMore ? "Loading..." : `Load more (${foods.length} of ${total})`}
          </Button>
        </div>
      )}
    </div>
  );
}
