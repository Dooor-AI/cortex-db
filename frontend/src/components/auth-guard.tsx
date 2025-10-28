'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Skip auth check for login page
    if (pathname === '/login') {
      setIsLoading(false);
      return;
    }

    // Check if API key exists
    const apiKey = localStorage.getItem('cortexdb_api_key');

    if (!apiKey) {
      router.push('/login');
      return;
    }

    // Verify the API key is still valid
    fetch('http://localhost:8000/api-keys', {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    })
      .then((res) => {
        if (res.ok) {
          setIsAuthenticated(true);
        } else {
          // Invalid key, redirect to login
          localStorage.removeItem('cortexdb_api_key');
          router.push('/login');
        }
      })
      .catch(() => {
        // Can't reach gateway, but let them try anyway
        setIsAuthenticated(true);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [pathname, router]);

  if (pathname === '/login') {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

