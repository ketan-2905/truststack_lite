/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Surface the API base URL to the browser.
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
