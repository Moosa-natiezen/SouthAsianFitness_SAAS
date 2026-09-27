import { render, screen } from "@testing-library/react";

import {
  FoodThumbnail,
  getFoodThumbnailVisual,
} from "@/components/food/food-thumbnail";

describe("food thumbnail mapping", () => {
  it("uses different category artwork for breads, grains, prepared dishes and sweets", () => {
    const categories = ["breads", "grains", "prepared-dishes", "sweeteners"];
    const visuals = categories.map((category) =>
      getFoodThumbnailVisual("South Asian food", "sample-food", category),
    );

    expect(new Set(visuals.map((visual) => visual.glyph)).size).toBe(
      categories.length,
    );
    expect(new Set(visuals.map((visual) => visual.background)).size).toBe(
      categories.length,
    );
  });

  it("infers a category from a food name when category metadata is missing", () => {
    expect(
      getFoodThumbnailVisual("whole wheat roti", "whole-wheat-roti", null)
        .category,
    ).toBe("Breads");
  });

  it("renders a fixed-layout accessible category thumbnail", () => {
    render(
      <FoodThumbnail
        name="Chicken biryani"
        slug="chicken-biryani"
        categorySlug="prepared-dishes"
      />,
    );

    expect(
      screen
        .getByRole("img", {
          name: "Chicken biryani prepared dishes thumbnail",
        })
        .getAttribute("data-category"),
    ).toBe("prepared-dishes");
  });
});
