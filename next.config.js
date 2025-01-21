/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: process.env.NODE_ENV === 'production' ? '/schengen-visa-appointment-bot' : '',
  images: {
    unoptimized: true,
  },
  assetPrefix: process.env.NODE_ENV === 'production' ? '/schengen-visa-appointment-bot/' : '',
  trailingSlash: true,
}

module.exports = nextConfig 