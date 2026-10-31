import type { NextConfig } from 'next';

const upstream = process.env.API_UPSTREAM ?? 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  devIndicators: false,
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${upstream}/api/:path*` }];
  },
};

export default nextConfig;
