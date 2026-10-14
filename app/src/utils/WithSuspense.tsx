import React, { Suspense } from 'react';
import BufferingWindow from '../components/BufferingWindow';

/** A fixed fallback, or one chosen from the route's props. Undefined keeps the default. */
type Fallback = React.ReactNode | ((props: any) => React.ReactNode);

export const WithSuspense = (Component: React.ComponentType<any>, fallback?: Fallback) => {
  return (props: any) => {
    const chosen = typeof fallback === 'function' ? fallback(props) : fallback;
    return (
      <Suspense fallback={chosen ?? <BufferingWindow testID="buffering-view" />}>
        <Component {...props} />
      </Suspense>
    );
  };
};
