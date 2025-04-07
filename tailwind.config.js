/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./**/templates/**/*.html",
    "./**/templates/**/**/*.html",

    "./src/*.js",
    "./src/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme primary colors based on #0b1f31
        primary: {
          50: "#edf2f7",
          100: "#dbe4ed",
          200: "#b7c9db",
          300: "#93adc9",
          400: "#6f92b7",
          500: "#4b76a5",
          600: "#3c5f84",
          700: "#2d4763",
          800: "#1e2f42",
          900: "#0f1721",
          950: "#0b1f31",
        },
        // Accent colors for visual interest
        secondary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#b9e6fe",
          300: "#7cd4fd",
          400: "#36bffa",
          500: "#0ba5ec",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
        // Status colors with dark theme compatibility
        success: {
          50: "#ecfdf5",
          500: "#10b981",
          600: "#059669",
        },
        warning: {
          50: "#fff7ed",
          500: "#ff9100",
          600: "#e68200",
        },
        info: {
          50: "#f0f9ff",
          500: "#00b0ff",
          600: "#0091ea",
        },
      },
      // Custom background patterns and gradients
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-dark":
          "linear-gradient(to bottom right, var(--tw-gradient-stops))",
        "squares-pattern":
          "url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMjk0MjVBIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')",
      },
      // Custom box shadows for depth
      boxShadow: {
        "dark-sm": "0 1px 2px 0 rgba(0, 0, 0, 0.35)",
        "dark-md": "0 4px 6px -1px rgba(0, 0, 0, 0.35)",
        "dark-lg":
          "0 10px 15px -3px rgba(0, 0, 0, 0.35), 0 4px 6px -2px rgba(0, 0, 0, 0.25)",
      },
      animation: {
        "spin-slow": "spin 2s linear infinite",
      },
    },
  },
  plugins: [],
};
