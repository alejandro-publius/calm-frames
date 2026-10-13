import React, { Suspense } from 'react';
import BufferingWindow from '../components/BufferingWindow';

export const WithSuspense = (Component: React.ComponentType<any>, fallback?: React.ReactNode) => {
  return (props: any) => (
    <Suspense fallback={fallback ?? <BufferingWindow testID="buffering-view" />}>
      <Component {...props} />
    </Suspense>
  );
};
