import React from 'react';

function LoadingSpinner() {
  return (
    <div className="flex justify-center items-center p-4">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
      <span className="ml-3 text-gray-600">Loading...</span>
    </div>
  );
}

export default LoadingSpinner; 