import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public paths that don't require authentication
  const publicPaths = ['/login'];

  if (publicPaths.includes(pathname)) {
    return NextResponse.next();
  }

  // Check if user has API key in cookie (for SSR) or will check localStorage (for CSR)
  // Since we're using localStorage, we'll handle this client-side
  // This middleware just ensures the login page is accessible
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)',
  ],
};

