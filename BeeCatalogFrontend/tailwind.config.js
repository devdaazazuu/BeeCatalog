export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        'radial-beams': "radial-gradient(circle at 80% 20%, rgba(240, 210, 60, 0.1), transparent 50%), radial-gradient(circle at 20% 80%, rgba(41, 95, 222, 0.1), transparent 50%)",
      }
    },
  },
  plugins: [],
}