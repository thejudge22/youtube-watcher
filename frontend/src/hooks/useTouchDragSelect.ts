import { useRef, useState, useCallback, useEffect } from 'react';

interface UseTouchDragSelectOptions {
  isEnabled: boolean;
  items: Array<{ id: string; element?: HTMLElement }>;
  selectedIds: Set<string>;
  lastClickedId: string | null;
  onSelectionChange: (newSelectedIds: Set<string>, newLastClickedId: string) => void;
}

interface UseTouchDragSelectReturn {
  containerRef: React.RefObject<HTMLDivElement>;
  isDragging: boolean;
  dragStartId: string | null;
  dragEndId: string | null;
  previewRange: Set<string>;
  getItemProps: (id: string) => {
    'data-video-id': string;
    onTouchStart: (e: React.TouchEvent) => void;
    onTouchMove: (e: React.TouchEvent) => void;
    onTouchEnd: (e: React.TouchEvent) => void;
  };
}

export function useTouchDragSelect({
  isEnabled,
  items,
  selectedIds: _selectedIds,
  lastClickedId: _lastClickedId,
  onSelectionChange,
}: UseTouchDragSelectOptions): UseTouchDragSelectReturn {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartId, setDragStartId] = useState<string | null>(null);
  const [dragEndId, setDragEndId] = useState<string | null>(null);
  const [previewRange, setPreviewRange] = useState<Set<string>>(new Set());
  const scrollIntervalRef = useRef<number | null>(null);

  // Find item index by ID
  const getItemIndex = useCallback((id: string) => {
    return items.findIndex(item => item.id === id);
  }, [items]);

  // Calculate range between two items
  const calculateRange = useCallback((startId: string, endId: string) => {
    const startIndex = getItemIndex(startId);
    const endIndex = getItemIndex(endId);

    if (startIndex === -1 || endIndex === -1) {
      return new Set<string>();
    }

    const start = Math.min(startIndex, endIndex);
    const end = Math.max(startIndex, endIndex);
    const range = new Set<string>();

    for (let i = start; i <= end; i++) {
      range.add(items[i].id);
    }

    return range;
  }, [items, getItemIndex]);

  // Update preview range based on current drag state
  const updatePreviewRange = useCallback((currentDragStartId: string | null, currentDragEndId: string | null) => {
    if (!currentDragStartId || !currentDragEndId) {
      setPreviewRange(new Set());
      return;
    }

    const range = calculateRange(currentDragStartId, currentDragEndId);
    setPreviewRange(range);
  }, [calculateRange]);

  // Handle touch start - begin drag selection
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!isEnabled || e.touches.length !== 1) {
      return;
    }

    const target = e.target as HTMLElement;
    const videoId = target.getAttribute('data-video-id');
    
    if (!videoId) {
      return;
    }

    // Prevent default scrolling behavior
    e.preventDefault();

    setIsDragging(true);
    setDragStartId(videoId);
    setDragEndId(videoId);
    
    // Update preview range immediately
    updatePreviewRange(videoId, videoId);
  }, [isEnabled, updatePreviewRange]);

  // Handle auto-scroll
  const handleAutoScroll = useCallback((clientY: number) => {
    const SCROLL_ZONE_HEIGHT = 50; // px
    const SCROLL_SPEED = 10; // px per tick
    const windowHeight = window.innerHeight;

    if (scrollIntervalRef.current) {
      cancelAnimationFrame(scrollIntervalRef.current);
      scrollIntervalRef.current = null;
    }

    const scroll = () => {
      let scrollAmount = 0;
      if (clientY < SCROLL_ZONE_HEIGHT) {
        // Scroll up
        scrollAmount = -SCROLL_SPEED;
      } else if (clientY > windowHeight - SCROLL_ZONE_HEIGHT) {
        // Scroll down
        scrollAmount = SCROLL_SPEED;
      }

      if (scrollAmount !== 0) {
        window.scrollBy(0, scrollAmount);
        scrollIntervalRef.current = requestAnimationFrame(scroll);
      }
    };

    scroll();
  }, []);

  // Handle touch move - update drag end position
  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isEnabled || !isDragging || e.touches.length !== 1) {
      return;
    }

    // Prevent default scrolling behavior during drag
    e.preventDefault();

    const touch = e.touches[0];
    const element = document.elementFromPoint(touch.clientX, touch.clientY);

    // Trigger auto-scroll
    handleAutoScroll(touch.clientY);
    
    if (!element) {
      return;
    }

    const videoId = element.getAttribute('data-video-id');
    
    if (videoId && videoId !== dragEndId) {
      setDragEndId(videoId);
      // We need to use dragStartId from state here, but it might be stale in this closure if not added to deps.
      // However, dragStartId only changes on touch start/end, so it should be stable during drag.
      // But let's use the functional update pattern or just rely on the dependency.
      updatePreviewRange(dragStartId, videoId);
    }
  }, [isEnabled, isDragging, dragEndId, dragStartId, updatePreviewRange, handleAutoScroll]);

  // Handle touch end - commit selection
  const handleTouchEnd = useCallback((_e: React.TouchEvent) => {
    if (!isEnabled || !isDragging) {
      return;
    }

    if (scrollIntervalRef.current) {
      cancelAnimationFrame(scrollIntervalRef.current);
      scrollIntervalRef.current = null;
    }

    if (dragStartId && dragEndId) {
      const range = calculateRange(dragStartId, dragEndId);
      
      // Update selection state
      onSelectionChange(range, dragEndId);
    }

    // Reset drag state
    setIsDragging(false);
    setDragStartId(null);
    setDragEndId(null);
    setPreviewRange(new Set());
  }, [isEnabled, isDragging, dragStartId, dragEndId, calculateRange, onSelectionChange]);

  // Cleanup scroll interval on unmount
  useEffect(() => {
    return () => {
      if (scrollIntervalRef.current) {
        cancelAnimationFrame(scrollIntervalRef.current);
      }
    };
  }, []);

  // Get item props for spreading on video elements
  const getItemProps = useCallback((id: string) => {
    return {
      'data-video-id': id,
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    containerRef,
    isDragging,
    dragStartId,
    dragEndId,
    previewRange,
    getItemProps,
  };
}
