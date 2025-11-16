// tailwind.config.cjs
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#06b6d4",
        charcoal: "#111827",
        offwhite: "#f8fafc"
      },
    }
  },
  plugins: []
};
