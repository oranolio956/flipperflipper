/**
 * Dashboard App - Main layout and navigation
 */

import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from '@/components/ui/toaster';
import { router } from './router';

export function App() {
  return (
    <>
      <RouterProvider router={router} />
      <Toaster />
    </>
  );
}