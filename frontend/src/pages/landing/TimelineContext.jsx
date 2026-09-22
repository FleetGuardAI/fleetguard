import React, { createContext, useContext, useRef, useState } from 'react';

const TimelineContext = createContext();

export function TimelineProvider({ children }) {
  const scrollContainerRef = useRef(null);
  const [theme, setTheme] = useState('dark');

  /**
   * Smoothly scrolls to a specific progress (0 to 1) along the master timeline container.
   */
  const seekTo = (progress) => {
    if (!scrollContainerRef.current) return;
    const container = scrollContainerRef.current;
    
    // We calculate the total scrollable distance of the container
    // offsetTop gets us the top of the container relative to the document
    // offsetHeight is the total height
    // window.innerHeight is the viewport height
    const scrollableDistance = container.offsetHeight - window.innerHeight;
    const targetScrollY = container.offsetTop + (scrollableDistance * progress);
    
    window.scrollTo({
      top: targetScrollY,
      behavior: 'smooth'
    });
  };

  return (
    <TimelineContext.Provider value={{ scrollContainerRef, seekTo, theme, setTheme }}>
      {children}
    </TimelineContext.Provider>
  );
}

export function useTimeline() {
  return useContext(TimelineContext);
}
