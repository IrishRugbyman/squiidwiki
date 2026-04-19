/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/templates/**/*.html",
    "./frontend/src/**/*.{js,ts}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f3e8ff",
          100: "#e4ccff",
          200: "#c99aff",
          300: "#a855f7",
          400: "#8b22e6",
          500: "#6a0dad",
          600: "#4a0072",
          700: "#3a0059",
          800: "#2a0040",
          900: "#1a0028",
        },
        surface: {
          DEFAULT: "#171717",
          light: "#ffffff",
        },
        bgbase: {
          DEFAULT: "#0a0a0a",
          light: "#f5f5f5",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [
    function ({ addVariant }) {
      addVariant("light", ".light &");
    },
  ],
};
